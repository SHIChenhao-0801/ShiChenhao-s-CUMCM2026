# Independent scalar checks with base R; no PDE solve or production changes.
out <- 'paper_output/qa/revision_20260913/formulas'
phi <- function(c,a) c*exp(-a/c)-a*integrate(function(u) exp(-u)/u,a/c,Inf,abs.tol=1e-14,rel.tol=1e-12)$value
records <- list()
for(a in c(.89,.45,.30)) for(limits in list(c(.05,.15),c(.15,.9),c(.9,2.55))) {
  left <- limits[1]; right <- limits[2]
  potential <- phi(right,a)-phi(left,a)
  quadrature <- integrate(function(c) exp(-a/c),left,right,abs.tol=1e-14,rel.tol=1e-12)$value
  records[[length(records)+1]] <- data.frame(a=a,left=left,right=right,potential_difference=potential,quadrature=quadrature,abs_difference=abs(potential-quadrature))
}
write.csv(do.call(rbind,records),file.path(out,'kirchhoff_checks.csv'),row.names=FALSE)
bi <- 25*.02/.36
f <- function(x) x*besselJ(x,1)-bi*besselJ(x,0)
grid <- seq(.001,35,length.out=7000)
roots <- list()
for(i in seq_len(length(grid)-1)) {
  if(f(grid[i])*f(grid[i+1])<0) {
    mu <- uniroot(f,c(grid[i],grid[i+1]),tol=1e-14)$root
    coefficient <- 2*besselJ(mu,1)/(mu*(besselJ(mu,0)^2+besselJ(mu,1)^2))
    projection <- integrate(function(x) x*besselJ(mu*x,0),0,1,abs.tol=1e-13)$value/integrate(function(x) x*besselJ(mu*x,0)^2,0,1,abs.tol=1e-13)$value
    roots[[length(roots)+1]] <- data.frame(mu=mu,robin_residual=f(mu),coefficient_formula=coefficient,coefficient_projection=projection,abs_difference=abs(coefficient-projection))
    if(length(roots)==8) break
  }
}
write.csv(do.call(rbind,roots),file.path(out,'bessel_checks.csv'),row.names=FALSE)
cat('Base R scalar checks complete. No PDE integration performed.\n')
