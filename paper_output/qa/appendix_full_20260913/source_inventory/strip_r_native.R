args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 3)
original <- readLines(args[1], encoding = "UTF-8", warn = FALSE)
before <- parse(text = original, keep.source = TRUE, encoding = "UTF-8")
tokens <- getParseData(before)
comments <- tokens[tokens$token == "COMMENT", ]
changed <- original
if (nrow(comments) > 0) {
  comments <- comments[order(comments$line1, comments$col1, decreasing = TRUE), ]
  for (j in seq_len(nrow(comments))) {
    item <- comments[j, ]
    stopifnot(item$line1 == item$line2)
    line <- changed[item$line1]
    prefix <- if (item$col1 > 1) substr(line, 1, item$col1 - 1) else ""
    suffix <- if (item$col2 < nchar(line)) substr(line, item$col2 + 1, nchar(line)) else ""
    changed[item$line1] <- paste0(prefix, suffix)
  }
}
changed <- sub("[ \t]+$", "", changed)
while (length(changed) > 0 && changed[1] == "") changed <- changed[-1]
after <- parse(text = changed, keep.source = TRUE, encoding = "UTF-8")
remaining <- getParseData(after)
stopifnot(sum(remaining$token == "COMMENT") == 0)
stopifnot(identical(parse(text = original, keep.source = FALSE, encoding = "UTF-8"), parse(text = changed, keep.source = FALSE, encoding = "UTF-8")))
writeLines(changed, args[2], useBytes = TRUE)
writeLines(c("parser=R native parse/getParseData", paste0("comment_count=",nrow(comments)), "remaining_comment_count=0", "parse_expression_equal_without_source=TRUE", "figure_execution=NOT_RERUN", paste0("R_version=",R.version.string)), args[3], useBytes=TRUE)
cat("R_PARSE_AND_EQUIVALENCE_PASS", nrow(comments), "comments\n")
