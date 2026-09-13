suppressWarnings(Sys.setlocale("LC_ALL", "Chinese_China.utf8"))
original <- parse("paper_output/figures/review_20260913/draw_figures.R", keep.source = FALSE)
adapted <- parse("paper_output/qa/support_completion_20260913/figures/adapted_before_comment_removal.R", keep.source = FALSE)
delivered <- parse("支撑材料/06_绘图程序与数据/draw_figures.R", keep.source = FALSE)
stopifnot(identical(adapted, delivered))
tokens <- getParseData(parse("支撑材料/06_绘图程序与数据/draw_figures.R", keep.source = TRUE))
stopifnot(!any(tokens$token == "COMMENT"))
assignments <- function(exprs) {
  result <- list()
  for (expr in exprs) {
    if (is.call(expr) && identical(expr[[1]], as.name("<-")) && is.name(expr[[2]])) {
      result[[as.character(expr[[2]])]] <- expr
    }
  }
  result
}
original_assign <- assignments(original)
delivered_assign <- assignments(delivered)
unchanged <- setdiff(names(original_assign), c("root", "input", "emit"))
stopifnot(all(vapply(unchanged, function(key) identical(original_assign[[key]], delivered_assign[[key]]), logical(1))))
calls <- function(exprs, names) {
  Filter(function(expr) is.call(expr) && is.name(expr[[1]]) && as.character(expr[[1]]) %in% names, as.list(exprs))
}
stopifnot(identical(calls(original, c("stopifnot", "for", "emit")), calls(delivered, c("stopifnot", "for", "emit"))))
cat("COMMENT_REMOVAL_AST_EQUIVALENT PASS\n")
cat("DELIVERED_COMMENT_TOKENS 0\n")
cat("UNCHANGED_ASSIGNMENTS", length(unchanged), paste(unchanged, collapse = ", "), "\n")
cat("NUMERIC_CHECKS_AND_SIX_EMIT_CALLS_IDENTICAL PASS\n")
cat("ORIGINAL_EXPRESSION_COUNT", length(original), "DELIVERED_EXPRESSION_COUNT", length(delivered), "\n")
