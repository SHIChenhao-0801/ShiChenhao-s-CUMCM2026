# 独立审查辅助，不执行被审源码，不写其结果目录。
library(Matrix)
root <- 'paper_output/results/a_restart'
a <- readRDS(file.path(root,'candidate_N80.rds')); b <- readRDS(file.path(root,'time_N80.rds'))
cat('same_N_time_field_difference',max(abs(a$u-b$u)),'\n')
a <- readRDS(file.path(root,'candidate_N160.rds'));b <- readRDS(file.path(root,'repeat_N160.rds'))
cat('repeat_array_identical',identical(a$u,b$u),'\n')
lam<-1.5; edges<-seq(0,1,length.out=161); t<-.37
avg<-sapply(seq_len(160),function(i) integrate(function(x) x*besselJ(lam*x,0)*exp(-lam^2*t),edges[i],edges[i+1],rel.tol=1e-12)$value/((edges[i+1]^2-edges[i]^2)/2))
h<-readRDS(file.path(root,'heldout_lambda1p5.rds'))
cat('quadrature_vs_stored_exact',max(abs(avg-h$exact)),'\n')
cat('quadrature_vs_numeric',max(abs(avg-h$u)),'\n')
n<-4; dx<-1/n; e<-seq(0,1,length.out=n+1); v<-diff(e^2)/2; bi<-besselJ(1,1)/besselJ(1,0); g<-e[2:n]/dx; w<-1/(dx/2+1/bi)
A<-sparseMatrix(i=c(seq_len(n),1:(n-1),2:n),j=c(seq_len(n),2:n,1:(n-1)),x=c(-(c(0,g)+c(g,w))/v,g/head(v,-1),g/tail(v,-1)),dims=c(n,n))
expected<-matrix(0,n,n)
for (j in 1:(n-1)) { expected[j,j]<-expected[j,j]-g[j]/v[j];expected[j,j+1]<-g[j]/v[j]; expected[j+1,j]<-g[j]/v[j+1];expected[j+1,j+1]<-expected[j+1,j+1]-g[j]/v[j+1] }
expected[n,n]<-expected[n,n]-w/v[n]
cat('matrix_face_assembly_difference',max(abs(as.matrix(A)-expected)),'\n')
cat('weighted_column_balance',max(abs(as.numeric(t(v)%*%A)-c(0,0,0,-w))),'\n')
cat('center_coefficient',A[1,2],'expected',2/dx^2,'\n')
u<-c(.9,.8,.7,.6);dt<-.001;nextu<-solve(diag(n)-dt*as.matrix(A)/2,(diag(n)+dt*as.matrix(A)/2)%*%u)
cat('CN_mass_identity',sum(v*(nextu-u))+dt*w*(u[n]+nextu[n])/2,'\n')
cat('Robin_exact_identity',abs(besselJ(1,1)-bi*besselJ(1,0)),'\n')
