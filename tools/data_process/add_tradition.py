import xlrd

#   打开参考文件
reference_file = xlrd.open_workbook(
    "reference.xls",
    encoding_override="gbk",
)
#   打开待处理文件
#   路径自己设置
target_file = xlrd.open_workbook(
    "target.xls",
    encoding_override="gbk",
)
output_file = open("output.txt", "w", encoding="utf-8")
#   取出sheeet
reference_sheet = reference_file.sheet_by_index(0)
target_sheet = target_file.sheet_by_index(0)

reference = {}
target = {}
#   取出参考文件的数据，建立字，繁体字映射关系
for i in range(1, reference_sheet.nrows):
    reference[reference_sheet.cell(i, 6).value] = reference_sheet.cell(i, 0).value
for i in range(1, target_sheet.nrows):
    target[target_sheet.cell(i, 0).value] = target_sheet.cell(i, 8).value
    if reference.__contains__(target_sheet.cell(i, 0).value):
        target[target_sheet.cell(i, 0).value] = reference[target_sheet.cell(i, 0).value]
for i in range(1, target_sheet.nrows):
    output_file.write(str(target.get(target_sheet.cell(i, 0).value)))
    output_file.write("\n")
    # 嗯，然后自个把繁体数据挪过去
output_file.close()
