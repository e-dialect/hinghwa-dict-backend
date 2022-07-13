import os
import re


def IPA_to_tone(IPA):
    try:
        matchObj = re.match(r"([^0-9]+)([0-9]*)$", IPA, re.M | re.I)
        return matchObj.group(2)
    except Exception:
        print("[寻找声调]这不是一个合法的IPA: ", IPA)
        return None


def IPA_to_shengmu(IPA):
    try:
        matchObj = re.match(r"([^0-9]+)([0-9]*)$", IPA, re.M | re.I)
        line = matchObj.group(1)  # 获取非声调部分
        matchObj = re.match(r"([^aeiouyɛøɒɔœ]*)(.*)$", line, re.M | re.I)
        sheng = matchObj.group(1)
        if line == "Ǿŋ":
            sheng = "Ǿ"
        if sheng == "":
            sheng = "Ǿ"
        return sheng
    except Exception:
        print("[寻找声母]这不是一个合法的IPA: ", IPA)
        return None


def IPA_to_yunmu(IPA):
    try:
        matchObj = re.match(r"([^0-9]+)([0-9]*)$", IPA, re.M | re.I)
        line = matchObj.group(1)  # 获取非声调部分
        matchObj = re.match(r"([^aeiouyɛøɒɔœ]*)(.*)$", line, re.M | re.I)
        yun = matchObj.group(2)
        if line == "Ǿŋ":
            yun = "ŋ"
        return yun
    except Exception:
        print("[寻找韵母]这不是一个合法的IPA: ", IPA)
        return None


def IPA_to_pinyin(IPA):
    try:
        sheng = IPA_to_shengmu(IPA)  # 声母
        yun = IPA_to_yunmu(IPA)  # 韵母
        tone = IPA_to_tone(IPA)  # 声调
        matchObj = re.match(r"(.*?)(ŋ?|n?|ʔ?)$", yun, re.M | re.I)
        yun1 = matchObj.group(1)  # 韵母元音
        yun2 = matchObj.group(2)  # 韵尾
        # 声母的处理
        if sheng == "p":
            sheng = "b"
        elif sheng == "ph":
            sheng = "p"
        elif sheng == "t":
            sheng = "d"
        elif sheng == "th":
            sheng = "t"
        elif sheng == "ts":
            sheng = "z"
        elif sheng == "tsh":
            sheng = "c"
        elif sheng == "k":
            sheng = "g"
        elif sheng == "kh":
            sheng = "k"
        elif sheng == "ɬ":
            sheng = "s"
        elif sheng == "ŋ":
            sheng = "ng"
        elif sheng == "Ǿ":
            sheng = ""  # 零声母Ǿ

        # 开尾韵或鼻化韵的处理
        if yun2 == "" or yun2 == "n":
            if yun1 == "ɛ":
                yun1 = "ae"
            elif yun1 == "ø":
                yun1 = "oe"
            elif yun1 == "ɒ":
                yun1 = "or"
            elif yun1 == "ɔu":
                yun1 = "ou"
            elif yun1 == "yɒ":
                yun1 = "yor"
            elif yun1 == "ɔ":
                yun1 = "or"
            elif yun1 == "yɔ":
                yun1 = "yor"

        # 塞尾韵或鼻尾韵的处理
        if yun2 == "ʔ" or yun2 == "ŋ":
            # 元音部分
            if yun1 == "ɛ":
                yun1 = "e"
            elif yun1 == "iɛ":
                yun1 = "ie"
            elif yun1 == "œ" or yun1 == "ø":
                yun1 = "oe"
            elif yun1 == "ɔ":
                yun1 = "or"
            elif yun1 == "ɒ":
                yun1 = "or"
            elif yun1 == "yɒ" or yun1 == "yɔ":
                yun1 = "yor"
            # 韵尾部分
            if yun2 == "ŋ":
                yun2 = "ng"
            elif yun2 == "ʔ":
                yun2 = "h"

        # 声调的处理
        if tone == "533":
            tone = "1"
        elif tone == "24" or tone == "13":
            tone = "2"
        elif tone == "453":
            tone = "3"
        elif tone == "42":
            tone = "4"
        elif tone == "11":
            tone = "5"
        elif tone == "2" or tone == "21":
            tone = "6"
        elif tone == "5" or tone == "4":
            tone = "7"

        return str(sheng + yun1 + yun2 + tone)
    except Exception:
        print("[翻译拼音]这不是一个合法的IPA: ", IPA)
        return None


if __name__ == "__main__":
    # data = []
    # for line in open("list.txt", "r"):  #设置文件对象并读取每一行文件
    #     data.append(line[0:-1])  #将每一行文件加入到list中
    # # print(data)
    # has = []
    # for filename in os.listdir(path='.'):
    #     if filename == "translate.py" or filename == "list.txt" or filename == "out.txt":
    #         continue
    #     matchObj = re.match(r'(.*).mp3$', filename, re.M | re.I)
    #     s = matchObj.group(1)  # 获取非声调部分
    #     has.append(s)

    # for i in data:
    #     flag = False
    #     for s in has:
    #         if i == s:
    #             flag = True
    #             break
    #     if flag == False:
    #         print(i)

    data = ["ai42", "bia42", "zai13", "e11", "yɒ13"]
    for i in data:
        print(IPA_to_pinyin(i))
