# 独立验证圆柱有限体积；未读取任何既有求解代码或结果。
suppressPackageStartupMessages(library(Matrix))
outDir <- "paper_output/results/a_restart"
dir.create(outDir, recursive=TRUE, showWarnings=FALSE)
batchStart <- Sys.time()
exactAverage <- function(edges, lambda, time) {
  a <- head(edges,-1); b <- tail(edges,-1)
  2*(b*besselJ(lambda*b,1)-a*besselJ(lambda*a,1))/
    (lambda*(b*b-a*a))*exp(-lambda^2*time)
}
runTrial <- function(id,n,dt,lambda=1,endTime=0.2,geometry="cylinder") {
  started <- Sys.time(); edges <- seq(0,1,length.out=n+1)
  dx <- 1/n; centers <- (head(edges,-1)+tail(edges,-1))/2
  bi <- lambda*besselJ(lambda,1)/besselJ(lambda,0)
  volume <- if(geometry=="cylinder") diff(edges^2)/2 else rep(dx,n)
  face <- if(geometry=="cylinder") edges else rep(1,n+1)
  conduct <- face[2:n]/dx
  # 最后半单元扩散电阻与外膜电阻串联。
  wallConduct <- 1/(dx/2+1/bi)
  diagonal <- -(c(0,conduct)+c(conduct,wallConduct))/volume
  op <- sparseMatrix(i=c(seq_len(n),1:(n-1),2:n),
    j=c(seq_len(n),2:n,1:(n-1)),
    x=c(diagonal,conduct/head(volume,-1),conduct/tail(volume,-1)),dims=c(n,n))
  steps <- ceiling(endTime/dt); actualDt <- endTime/steps
  left <- Diagonal(n)-actualDt*op/2
  right <- Diagonal(n)+actualDt*op/2
  fact <- lu(left)
  u <- exactAverage(edges,lambda,0)
  initialMass <- sum(volume*u); lost <- 0
  minimum <- min(u)
  for(step in seq_len(steps)) {
    previous <- u
    u <- as.numeric(solve(fact,as.numeric(right%*%u)))
    lost <- lost+actualDt*wallConduct*(tail(previous,1)+tail(u,1))/2
    minimum <- min(minimum,u)
  }
  target <- exactAverage(edges,lambda,endTime)
  residual <- sum(volume*u)+lost-initialMass
  if(any(!is.finite(u))) stop("nonfinite result")
  row <- data.frame(id=id,n=n,dt=actualDt,lambda=lambda,endTime=endTime,
    geometry=geometry,steps=steps,maxAbsError=max(abs(u-target)),
    massResidual=residual,minValue=minimum,
    elapsedSeconds=as.numeric(difftime(Sys.time(),started,units="secs")),
    startedUtc=format(started,tz="UTC",usetz=TRUE),
    endedUtc=format(Sys.time(),tz="UTC",usetz=TRUE),exitCode=0)
  saveRDS(list(row=row,edges=edges,u=u,exact=target),file.path(outDir,paste0(id,".rds")))
  cat(id,"error",format(row$maxAbsError,digits=12),"mass",format(residual,digits=12),"\n")
  list(row=row,u=u)
}
trials <- list(
  runTrial("baseline_N20",20,.002),
  runTrial("candidate_N40",40,.001),
  runTrial("candidate_N80",80,.00025),
  runTrial("candidate_N160",160,.0000625),
  runTrial("negative_flat_N40",40,.001,geometry="flat"),
  runTrial("time_N80",80,.000125),
  runTrial("repeat_N160",160,.0000625))
validRows <- do.call(rbind,lapply(trials,`[[`,"row"))
eligible <- validRows$geometry=="cylinder" & abs(validRows$massResidual)<1e-10 & validRows$minValue>0
best <- which.min(ifelse(eligible,validRows$maxAbsError,Inf))
bestId <- validRows$id[best]
# 选择冻结之后执行留出，不使用留出优化候选。
hold <- runTrial("heldout_lambda1p5",validRows$n[best],validRows$dt[best],lambda=1.5,endTime=.37)
allRows <- rbind(validRows,hold$row)
allRows$decision <- ifelse(allRows$geometry!="cylinder","discard_wrong_geometry",
  ifelse(allRows$id==bestId,"keep_best",ifelse(allRows$id=="heldout_lambda1p5","heldout_check","valid_record")))
write.csv(allRows,file.path(outDir,"trials.csv"),row.names=FALSE)
repeatError <- max(abs(trials[[4]]$u-trials[[7]]$u))
# 非线性制造函数C=1+x²、D=1+C；通量散度为8+8x²。
x <- seq(.05,.95,length.out=19); eps <- 1e-5
flux <- function(x) x*(2+x*x)*2*x
fd <- (flux(x+eps)-flux(x-eps))/(2*eps*x)
correct <- 8+8*x*x; wrong <- 8+4*x*x
# 收缩材料坐标：R=exp(-a*t)，C=exp(-t)*(1+(r/R)^2)。
a <- .1; t <- .7; R <- exp(-a*t); r <- .4*R
atFixedR <- exp(-t)*(-(1+(r/R)^2)+2*a*(r/R)^2)
advection <- (-a*r)*exp(-t)*2*r/R^2
atFixedX <- -exp(-t)*(1+.4^2)
checks <- data.frame(check=c("repeat_equal","nonlinear_flux_derivative",
  "omitted_gradient_detected","moving_chain_rule","mass_balance","heldout_error"),
  metric=c(repeatError,max(abs(fd-correct)),max(abs(wrong-correct)),
    abs(atFixedR+advection-atFixedX),max(abs(allRows$massResidual)),hold$row$maxAbsError),
  pass=c(repeatError==0,max(abs(fd-correct))<1e-6,max(abs(wrong-correct))>1,
    abs(atFixedR+advection-atFixedX)<1e-12,max(abs(allRows$massResidual))<1e-10,
    hold$row$maxAbsError<1e-4))
write.csv(checks,file.path(outDir,"checks.csv"),row.names=FALSE)
# 只采用原题常数计算量级；Lv、辐射参数明确是情景。
property <- function(q,C,T) {
 if(q==1) return(c(rho=820,cp=2600,k=.36,D=7e-9*exp(-.89/C)))
 if(q==23) return(c(rho=650+128*C,cp=1450+2736*C/(1+C),k=.21+.38*C/(1+C),D=2.4e-3*exp(-.45/C-3850/T)))
 c(rho=760+90*C,cp=1850+2150*C/(1+C),k=.12+.20*C/(1+C),D=4.2e-4*exp(-.30/C-3850/T))
}
scales <- do.call(rbind,lapply(c(1,23,4),function(q) do.call(rbind,lapply(c(2.55,.15),function(C) {
 T <- if(C==2.55)301.15 else 323.15; p <- property(q,C,T); alpha<-p['k']/(p['rho']*p['cp'])
 data.frame(q=q,C=C,T=T,rho=p['rho'],cp=p['cp'],k=p['k'],D=p['D'],
   alpha=alpha,BiHeat=25*.02/p['k'],BiMass=8e-7*.02/p['D'],
   radialHeatSeconds=.02^2/alpha,radialMassHours=.02^2/p['D']/3600)
}))))
write.csv(scales,file.path(outDir,"scales.csv"),row.names=FALSE)
info <- c(capture.output(sessionInfo()),paste("best_id",bestId),
  paste("random_seed","not_applicable_deterministic"),
  paste("batch_started_utc",format(batchStart,tz="UTC",usetz=TRUE)),
  paste("batch_ended_utc",format(Sys.time(),tz="UTC",usetz=TRUE)),
  paste("elapsed_seconds",as.numeric(difftime(Sys.time(),batchStart,units="secs"))))
writeLines(info,file.path(outDir,"environment.txt"))
stopifnot(all(checks$pass))
cat("ALL_CHECKS_PASS; best:",bestId,"\n")
