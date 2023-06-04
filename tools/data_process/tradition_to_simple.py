import zhconv
import xlrd


workbook = xlrd.open_workbook(
    "target.xls",  # todo 自定义
    encoding_override="gbk",
)
output_file = open("output.txt", "w", encoding="utf-8")
#   取出sheeet
workbook_sheet = workbook.sheet_by_index(0)


#   取出参考文件的数据，建立字，繁体字映射关系
for i in range(1, workbook_sheet.nrows):
    output_file.write(zhconv.convert(workbook_sheet.cell(i, 8).value, "zh-cn"))
    output_file.write("\n")

output_file.close()
