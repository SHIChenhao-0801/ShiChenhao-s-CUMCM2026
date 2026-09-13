# Reproduce six paper figures using frozen exported CSV data only.
# Run from D:/Document/数学建模/2026CUMCM with Rscript --vanilla.
options(warn = 1)
suppressWarnings(Sys.setlocale("LC_ALL", "Chinese_China.utf8"))
args_all <- commandArgs(trailingOnly = FALSE)
script_arg <- args_all[startsWith(args_all, "--file=")]
if (length(script_arg) != 1L) stop("Run this file with Rscript --vanilla.")
root <- dirname(normalizePath(sub("^--file=", "", script_arg), winslash = "/", mustWork = TRUE))
input <- file.path(root, "CSV")
args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0L) {
  output <- file.path(root, "PNG")
} else if (length(args) == 2L && args[1] == "--output-dir") {
  output <- args[2]
} else {
  stop("Usage: Rscript --vanilla draw_figures.R [--output-dir DIRECTORY]")
}
dir.create(output, recursive = TRUE, showWarnings = FALSE)
output <- normalizePath(output, winslash = "/", mustWork = TRUE)
font_cn <- "Microsoft YaHei"
font_math <- "Times New Roman"
palette7 <- c("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#A97700", "#56B4E9", "#414141")
ltypes7 <- c("solid", "dashed", "dotted", "dotdash", "longdash", "twodash", "1343")
shape7 <- c(16, 17, 15, 18, 1, 2, 0)
read_table <- function(fig, name) read.csv(file.path(input, paste0("图", fig), name), fileEncoding = "UTF-8-BOM", check.names = FALSE)

theme <- function(oma = c(3.8, 0.4, 0.4, 0.4), mar = c(3.5, 4.0, 2.0, 1.0)) {
  par(family = font_cn, ps = 10, cex = 1, cex.axis = 0.86, cex.lab = 0.97,
      las = 1, mgp = c(2.25, 0.62, 0), tcl = -0.25, bty = "l", xaxs = "i",
      yaxs = "i", lend = "round", fg = "#333333", col.axis = "#333333",
      col.lab = "#242424", oma = oma, mar = mar)
}
panel <- function(xlim, ylim, xticks, yticks, title, xlab, ylab, ylabels = NULL, log = "") {
  plot.new(); plot.window(xlim, ylim, log = log)
  abline(h = yticks, col = "#E3E7EA", lwd = 0.55)
  axis(1, at = xticks, labels = xticks, lwd = 0, lwd.ticks = 0.6)
  axis(2, at = yticks, labels = if (is.null(ylabels)) yticks else ylabels, lwd = 0, lwd.ticks = 0.6)
  box(bty = "l", lwd = 0.65)
  mtext(title, 3, line = 0.65, adj = 0, cex = 1.0, font = 2, family = font_cn)
  mtext(xlab, 1, line = 2.05, cex = 1.0, family = if(is.expression(xlab)) font_math else font_cn)
  mtext(ylab, 2, line = 2.6, las = 0, cex = 1.0, family = if(is.expression(ylab)) font_math else font_cn)
}
footer <- function(labels, cols, ltys, pchs = NULL, ncol = length(labels), title = NULL, cex = 0.84, y = 0.082) {
  par(fig = c(0, 1, 0, 1), mar = c(0, 0, 0, 0), oma = c(0, 0, 0, 0), new = TRUE)
  plot.new(); plot.window(c(0,1), c(0,1))
  legend(0.5, y, labels, col = cols, lty = ltys, pch = pchs, lwd = 1.5,
         ncol = ncol, bty = "n", xjust = 0.5, yjust = 0.5, cex = cex,
         x.intersp = 0.6, y.intersp = 1.12, seg.len = 2.4, title = title, title.adj = 0.5)
}
note <- function(text, line = 0.15, cex = 0.77) mtext(text, 1, outer = TRUE, line = line, cex = cex, col = "#4D555B")
emit <- function(name, draw, width = 7.2, height = 4.6) {
  png(file.path(output, paste0(name, ".png")), width = width, height = height, units = "in", res = 300, type = "cairo", bg = "white", family = font_cn, pointsize = 10)
  draw(); dev.off()
  cat("WROTE", name, "PNG 300 dpi\n")
}

f1t <- read_table(1, "temperature.csv"); f1c <- read_table(1, "moisture.csv")
f2o <- read_table(2, "observed_0_4h.csv"); f2p <- read_table(2, "assumed_platform_4_60h.csv")
f3t <- read_table(3, "temperature_0_4h.csv"); f3c <- read_table(3, "moisture_to_event.csv")
f4 <- read_table(4, "drying_main.csv"); f4near <- read_table(4, "maximum_near_event.csv"); f4events <- read_table(4, "event_markers.csv")
f4centre <- read_table(4, "centre_near_event.csv")
f5r <- read_table(5, "radius_observed.csv"); f5c <- read_table(5, "moisture_profiles_xy_pairs.csv"); f5sel <- read_table(5, "selected_times_and_radii.csv")
f6 <- read_table(6, "scenario_comparison.csv")

# Data invariants important to scientific interpretation of these plots.
stopifnot(nrow(f1t)==121, nrow(f1c)==121, nrow(f2o)==241, nrow(f5sel)==6,
          tail(f2o$time_h,1)==4, tail(f2o$temperature_C,1)==50.165,
          tail(f2o$air_moisture_kg_per_kg,1)==0.04986,
          f2p$endpoint_included[1]==0, nrow(f4near)==2, nrow(f4events)==2,
          f4events$max_C_minus_threshold[2]<0, identical(f6$p, c(1L,2L,4L)))
for (j in 1:6) stopifnot(abs(tail(f5c[[2*j-1]],1)-f5sel$radius_cm[j]) < 1e-12)
cat("DATA CHECKS PASS: original endpoint / open platform / event values / six distinct radii / six N800 scenario points\n")
checks <- list(
  c("f1_T", range(as.matrix(f1t[-1])), 27.7, 37.5),
  c("f1_C", range(as.matrix(f1c[-1])), 1.45, 2.6),
  c("f2_T", range(f2o$temperature_C), 24, 52.5),
  c("f2_air_indicator", range(f2o$air_moisture_kg_per_kg), .018, .0525),
  c("f3_T", range(as.matrix(f3t[-1])), 26, 52),
  c("f3_C", range(as.matrix(f3c[-1])), 0, 2.65),
  c("f4_C_log_axis", range(as.matrix(f4[c("centre_C","surface_C","max_C")])), .04, 3),
  c("f4_delta_scaled", range(c(f4near$max_C_minus_threshold, f4events$max_C_minus_threshold))*1e7, -5.45, .8),
  c("f5_R", range(f5r$radius_cm), 1.16, 2.04),
  c("f5_C_log_axis", range(as.matrix(f5c[seq(2,12,2)])), .04, 3),
  c("f6_time", range(as.matrix(f6[-1])), 49, 68)
)
bounds <- as.data.frame(do.call(rbind,checks),stringsAsFactors=FALSE)
names(bounds) <- c("panel","data_min","data_max","axis_min","axis_max")
for(j in 2:5) bounds[[j]] <- as.numeric(bounds[[j]])
bounds$all_data_in_range <- bounds$data_min >= bounds$axis_min & bounds$data_max <= bounds$axis_max
stopifnot(all(bounds$all_data_in_range))
print(bounds, row.names = FALSE)
cat("DATA RANGE CHECKS PASS: all 11 plotted data ranges fully visible\n")

draw1 <- function() {
  layout(matrix(1:2, 1, 2)); theme(oma = c(4.0,0.4,0.5,0.4))
  panel(c(0,2), c(27.7,37.5), seq(0,2,0.5), seq(28,36,2), "(a) 径向温度", expression(italic(r)~"/ cm"), expression(italic(T)~"/"*degree*C))
  for(j in 1:7) lines(f1t$r_cm, f1t[[j+1]], col=palette7[j], lty=ltypes7[j], lwd=1.55)
  panel(c(0,2), c(1.45,2.6), seq(0,2,0.5), seq(1.5,2.5,0.2), "(b) 径向干基含水率", expression(italic(r)~"/ cm"), expression(italic(C)~"/ (kg/kg)"), sprintf("%.1f",seq(1.5,2.5,0.2)))
  for(j in 1:7) lines(f1c$r_cm, f1c[[j+1]], col=palette7[j], lty=ltypes7[j], lwd=1.55)
  footer(c("100", "300", "600", "900", "1200", "1500", "1800"), palette7, ltypes7, ncol=7, title="时间 / s", y=0.083)
}

draw2 <- function() {
  layout(matrix(1:4,2,2,byrow=TRUE), widths=c(1.25,1)); theme(oma=c(3.2,0.4,0.4,0.4), mar=c(3.3,4.4,2.0,0.9))
  panel(c(0,4.12), c(24,52.5), 0:4, seq(25,50,5), "(a) 0–4 h：环境温度", expression(italic(t)~"/ h"), expression(italic(T)[plain(a)]~"/"*degree*C))
  lines(f2o$time_h, f2o$temperature_C, col=palette7[1], lwd=1.1)
  points(f2o$time_h, f2o$temperature_C, col=palette7[1], pch=16, cex=0.20)
  abline(v=4,lty=3,col="#8A9297"); points(4,50.165,pch=16,cex=0.65,col=palette7[1])
  text(2.15,43.8,"4 h末值：50.165 °C",cex=0.77,adj=0)
  panel(c(0,60), c(24,52.5), seq(0,60,20), seq(25,50,5), "(b) 延拓至 60 h", expression(italic(t)~"/ h"), expression(italic(T)[plain(a)]~"/"*degree*C))
  rect(4,24,60,52.5,col="#F2F5F7",border=NA); abline(h=seq(25,50,5),col="#E3E7EA",lwd=.55)
  lines(f2o$time_h,f2o$temperature_C,col=palette7[1],lwd=1.2)
  lines(f2p$time_h,f2p$temperature_C,col=palette7[2],lty=2,lwd=1.6)
  points(4,50,pch=21,bg="white",col=palette7[2],cex=.65)
  abline(v=4,lty=3,col="#8A9297"); text(34,42,"t > 4 h：50 °C",cex=.82)
  panel(c(0,4.12), c(.018,.0525), 0:4, seq(.02,.05,.01), "(c) 0–4 h：空气水分指标", expression(italic(t)~"/ h"), "空气水分指标 / (kg/kg)",sprintf("%.2f",seq(.02,.05,.01)))
  lines(f2o$time_h,f2o$air_moisture_kg_per_kg,col=palette7[1],lwd=1.1)
  points(f2o$time_h,f2o$air_moisture_kg_per_kg,col=palette7[1],pch=16,cex=.20)
  abline(v=4,lty=3,col="#8A9297"); points(4,.04986,pch=16,cex=.65,col=palette7[1])
  text(1.8,.035,"4 h末值：0.04986 kg/kg",cex=.77,adj=0)
  panel(c(0,60), c(.018,.0525), seq(0,60,20), seq(.02,.05,.01), "(d) 延拓至 60 h", expression(italic(t)~"/ h"), "空气水分指标 / (kg/kg)",sprintf("%.2f",seq(.02,.05,.01)))
  rect(4,.018,60,.0525,col="#F2F5F7",border=NA); abline(h=seq(.02,.05,.01),col="#E3E7EA",lwd=.55)
  lines(f2o$time_h,f2o$air_moisture_kg_per_kg,col=palette7[1],lwd=1.2)
  lines(f2p$time_h,f2p$boundary_moisture_kg_per_kg,col=palette7[2],lty=2,lwd=1.6)
  points(4,.05,pch=21,bg="white",col=palette7[2],cex=.65)
  abline(v=4,lty=3,col="#8A9297"); text(34,.035,"t > 4 h：0.05 kg/kg",cex=.82)
  footer(c("观测及分段线性插值","假设平台（左端开放）"),palette7[1:2],c(1,2),pchs=c(16,1),ncol=2,y=.046,cex=.84)
}

draw3 <- function() {
  layout(matrix(1:2,1,2)); theme(oma=c(3.25,0.4,0.5,0.4))
  panel(c(0,4),c(26,52),0:4,seq(30,50,5),"(a) 前 4 h 的温度响应",expression(italic(t)~"/ h"),expression(italic(T)~"/"*degree*C))
  lines(f3t$time_h,f3t$centre_T_C,col=palette7[1],lwd=1.7)
  lines(f3t$time_h,f3t$surface_T_C,col=palette7[2],lty=2,lwd=1.7)
  panel(c(0,60),c(0,2.65),seq(0,60,12),seq(0,2.5,.5),"(b) 全过程干基含水率",expression(italic(t)~"/ h"),expression(italic(C)~"/ (kg/kg)"),sprintf("%.1f",seq(0,2.5,.5)))
  abline(h=.15,col="#777777",lty=3,lwd=1)
  lines(f3c$time_h,f3c$centre_C_kg_per_kg,col=palette7[1],lwd=1.7)
  lines(f3c$time_h,f3c$surface_C_kg_per_kg,col=palette7[2],lty=2,lwd=1.7)
  text(39,.30,"阈值 0.15",cex=.8,adj=0,col="#646464")
  footer(c("中心（r = 0）","表面（r = 2 cm）"),palette7[1:2],c(1,2),ncol=2,y=.067,cex=.9)
}

draw4 <- function() {
  layout(matrix(1:2,1,2),widths=c(1.1,1)); theme(oma=c(4.1,0.4,0.6,0.4),mar=c(3.5,4.1,2.1,1))
  panel(c(0,60),c(.04,3),seq(0,60,12),c(.05,.1,.2,.5,1,2),"(a) 达标过程（对数刻度）",expression(italic(t)~"/ h"),expression(italic(C)~"/ (kg/kg)"),c("0.05","0.1","0.2","0.5","1","2"),log="y")
  abline(h=.15,col="#777777",lty=3,lwd=1)
  lines(f4$time_h,f4$max_C,col="#303030",lwd=2.0)
  lines(f4$time_h,f4$centre_C,col=palette7[1],lty=2,lwd=1.6)
  lines(f4$time_h,f4$surface_C,col=palette7[2],lty=1,lwd=1.6)
  points(f4events$time_h[1],.15,col="#303030",bg="white",pch=21,cex=.85)
  text(7,.18,"阈值 0.15",cex=.78,adj=0,col="#606060")
  text(17,1.5,"中心与全域最大值重合",cex=.78,adj=0,col=palette7[1])
  panel(c(-.07,1.8),c(-5.45,.8),c(0,.4,.8,1.2,1.6),seq(-5,0,1),"(b) 临界时刻附近",expression((italic(t)-italic(t)[plain(c)])~"/ s"),expression((italic(M)-0.15)~"/"~(10^{-7}~"kg/kg")))
  abline(h=0,col="#777777",lty=3,lwd=1)
  lines(f4near$delta_time_s,f4near$max_C_minus_threshold*1e7,col="#6C747A",lty=3,lwd=1.1)
  points(f4near$delta_time_s,f4near$max_C_minus_threshold*1e7,pch=22,bg="#6C747A",col="#6C747A",cex=.8)
  points(f4events$delta_time_s[1],f4events$max_C_minus_threshold[1]*1e7,pch=21,bg="white",col="#222222",cex=1.05,lwd=1.25)
  points(f4events$delta_time_s[2],f4events$max_C_minus_threshold[2]*1e7,pch=17,col=palette7[3],cex=1.1)
  text(.20,.43,expression(italic(t)[plain(c)]),adj=0,cex=.95,family=font_math)
  text(.52,-.94,expression(italic(t)[plain(r)]),adj=0,cex=.95,family=font_math,col=palette7[3])
  text(.10,-4.2,"临界时刻：57.472302 h\n核验时刻：57.4724 h\n二者相差：0.352978 s",adj=0,cex=.78)
  footer(c("全域最大值 M(t)","中心","表面","临界等号根","严格达标取值"),c("#303030",palette7[1],palette7[2],"#222222",palette7[3]),c(1,2,1,NA,NA),pchs=c(NA,NA,NA,1,17),ncol=3,y=.080,cex=.80)
}

draw5 <- function() {
  layout(matrix(1:2,1,2)); theme(oma=c(4.0,.4,.5,.4),mar=c(3.5,4.0,2.0,1))
  panel(c(0,72),c(1.16,2.04),seq(0,72,12),seq(1.2,2,.2),"(a) 收缩半径与选定时刻",expression(italic(t)~"/ h"),expression(italic(R)~"/ cm"))
  lines(f5r$time_h,f5r$radius_cm,col="#69757D",lwd=1.5)
  for(j in 1:6) points(f5sel$time_h[j],f5sel$radius_cm[j],col=palette7[j],bg="white",pch=shape7[j],cex=.85,lwd=1.3)
  text(29,1.81,"后期半径接近 1.2 cm",cex=.78,adj=0)
  panel(c(0,2.04),c(.04,3),seq(0,2,.5),c(.05,.1,.2,.5,1,2),"(b) 含水率（对数刻度）",expression(italic(r)~"/ cm"),expression(italic(C)~"/ (kg/kg)"),c("0.05","0.1","0.2","0.5","1","2"),log="y")
  for(j in 1:6) {
    xx <- f5c[[2*j-1]]; yy <- f5c[[2*j]]
    lines(xx,yy,col=palette7[j],lty=ltypes7[j],lwd=1.55)
    points(tail(xx,1),tail(yy,1),col=palette7[j],pch=shape7[j],cex=.85,lwd=1.2)
  }
  text(1.63,.16,"曲线止于各自表面\n表面以点形标出",cex=.76)
  footer(c("0 h","6 h","12 h","24 h","48 h","临界 51.090575 h"),palette7[1:6],ltypes7[1:6],shape7[1:6],ncol=3,y=.08,cex=.85)
}

draw6 <- function() {
  layout(matrix(1)); theme(oma=c(2.5,.3,.4,.3),mar=c(3.7,4.0,2.2,1.2))
  panel(c(.82,4.18),c(49,68),c(1,2,4),seq(50,68,3),"经验边界阻力情景下的临界时长",expression(italic(p)),expression(italic(t)[plain(c)]~"/ h"))
  lines(f6$p,f6$Q23_event_h,col=palette7[1],lwd=1.7)
  lines(f6$p,f6$Q4_event_h,col=palette7[2],lty=2,lwd=1.7)
  points(f6$p,f6$Q23_event_h,col=palette7[1],pch=16,cex=.85)
  points(f6$p,f6$Q4_event_h,col=palette7[2],pch=17,cex=.95)
  text(f6$p,f6$Q23_event_h+.65,sprintf("%.4f",f6$Q23_event_h),col=palette7[1],cex=.83)
  text(f6$p,f6$Q4_event_h-.75,sprintf("%.4f",f6$Q4_event_h),col=palette7[2],cex=.83)
  legend("topleft",c("固定半径，附录3物性","径向收缩，附录4物性"),col=palette7[1:2],lty=c(1,2),pch=c(16,17),lwd=1.7,bty="n",cex=.9,y.intersp=1.2)
  note("统一采用 N = 800、零潜热负荷；该经验参数族未经实测等温线标定。",line=.5,cex=.82)
}

emit("图1_径向温度与含水率",draw1,7.2,4.6)
emit("图2_环境观测与平台延拓",draw2,7.2,5.9)
emit("图3_中心与表面热湿响应",draw3,7.2,4.5)
emit("图4_全域达标与临界放大",draw4,7.2,4.9)
emit("图5_收缩半径与域内含水率",draw5,7.2,4.6)
emit("图6_经验边界阻力情景",draw6,7.2,4.6)



print(data.frame(metric=c("figure_count","input_csv_count","input_data_rows","figure4_report_delta_s","figure4_report_M_minus_threshold","figure4_max_centre_difference","figure4_saved_endpoint_h","new_pde_runs"),
  value=c(6,14,4627,f4events$delta_time_s[2],f4events$max_C_minus_threshold[2],max(abs(f4$max_C-f4$centre_C)),max(f4$time_h),0)),
  row.names=FALSE)
print(sessionInfo())
cat("DONE. Six PNG figures generated from the supplied CSV data.\n")
