# coding=utf-8
from tools.data_process import translate
import xlrd
import xlwt

# 打开一个workbook
workbook = xlrd.open_workbook("./3.xls")
worksheet1 = workbook.sheets()[0]

outbook = xlwt.Workbook()  # 注意Workbook的开头W要大写
out = outbook.add_sheet("sheet1", cell_overwrite_ok=True)

import re


def mycmp(str1, str2):
    return str1 < str2


def fenpinyin(pinyin):
    try:
        pinyin = str(pinyin)

        if pinyin.find("…") or pinyin.find("（") or pinyin.find("）"):
            fuhao = re.split("([…（）])", pinyin)
        else:
            fuhao = {pinyin}
        ss = ""
        for sss in fuhao:
            if sss in {"…", "（", "）"}:
                ss = ss + sss + " "
                continue

            s = re.split("(\d)", sss)

            for i in range(0, len(s) - 1, 2):
                p = list(translate.mohuyin(s[i] + s[i + 1]))
                if len(p) != 1:
                    ans = ""
                    flag = 0
                    for ts in p:
                        if ts == s[i] + s[i + 1]:
                            ans = ts
                            flag = 1
                    if flag == 1 and ans != "":
                        ss = ss + str(ans) + " "
                    else:
                        print("原来切分出来" + s[i] + s[i + 1])
                        print(p)
                        print(ans + "-----------")
                        print(pinyin)
                        ss = "--------------------"

                else:
                    ss = ss + p[0] + " "
        return ss
    except Exception as e:
        print(e)
        print(pinyin)


def fenIPA(pinyin):
    try:
        pinyin = str(pinyin)

        if pinyin.find("…") or pinyin.find("（") or pinyin.find("）"):
            fuhao = re.split("([…（）])", pinyin)
        else:
            fuhao = {pinyin}
        ss = ""
        for sss in fuhao:
            if sss in {"…", "（", "）"}:
                ss = ss + sss + " "
                continue

            s = re.split("(\d+)", sss)

            for i in range(0, len(s) - 1, 2):
                ss = ss + s[i] + s[i + 1] + " "
        return ss
    except Exception as e:
        print(e)
        print(pinyin)


# 遍历sheet1中所有行row
num_rows = worksheet1.nrows
for row in range(num_rows):
    out.write(row, 0, worksheet1.cell_value(row, 0))
    out.write(row, 3, worksheet1.cell_value(row, 3))
    pinyin = worksheet1.cell_value(row, 1)
    IPA = worksheet1.cell_value(row, 2)
    out.write(row, 1, fenpinyin(pinyin))
    out.write(row, 2, fenIPA(IPA))

# 保存该excel文件,有同名文件时直接覆盖
outbook.save("./4.xls")
