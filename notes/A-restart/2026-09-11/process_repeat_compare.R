firstRoot <- 'paper_output/results/a_restart'
repeatRoot <- file.path(firstRoot,'process_repeat_root/paper_output/results/a_restart')
ids <- c('baseline_N20','candidate_N40','candidate_N80','candidate_N160','negative_flat_N40','time_N80','repeat_N160','heldout_lambda1p5')
rows<-do.call(rbind,lapply(ids,function(id) {
 a<-readRDS(file.path(firstRoot,paste0(id,'.rds')));b<-readRDS(file.path(repeatRoot,paste0(id,'.rds')))
 data.frame(id=id,numericCount=length(a$u),uIdentical=identical(a$u,b$u),exactIdentical=identical(a$exact,b$exact),edgesIdentical=identical(a$edges,b$edges),maxUAbsDifference=max(abs(a$u-b$u)),maxExactAbsDifference=max(abs(a$exact-b$exact)))
}))
write.csv(rows,file.path(firstRoot,'process_repeat_root/process_repeat_compare.csv'),row.names=FALSE)
print(rows)
stopifnot(all(rows$uIdentical),all(rows$exactIdentical),all(rows$edgesIdentical))
cat('ALL_EIGHT_TRIALS_ARRAYS_IDENTICAL\n')

