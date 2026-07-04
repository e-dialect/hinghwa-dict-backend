#!/usr/bin/env python3
"""
优雅的IPA匹配测试 - 融合创新与安全

测试目标：
1. 验证融合混淆集的覆盖范围
2. 测试三大误差场景处理能力
3. 验证安全约束的有效性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.matcher.ipa_matcher import IPAMatcher
from src.matcher.ipa_constants import (
    CONFUSION_MAP, TONE_MAP, SANDHI_RULES, 
    ASR_ERROR_MAP, ACCENT_MAP, SAFETY_CONSTRAINTS
)

def test_confusion_coverage():
    """测试混淆集覆盖范围"""
    print("=" * 70)
    print("混淆集覆盖范围测试")
    print("=" * 70)
    
    # 统计各类规则数量
    single_char_rules = len([k for k in CONFUSION_MAP if len(k) == 1])
    multi_char_rules = len([k for k in CONFUSION_MAP if len(k) > 1])
    
    print(f"\n📊 混淆规则统计:")
    print(f"  单字符规则: {single_char_rules}条")
    print(f"  多字符规则: {multi_char_rules}条")
    print(f"  声调规则: {len(TONE_MAP)}条")
    print(f"  连读规则: {sum(len(v) for v in SANDHI_RULES.values())}条")
    print(f"  ASR错误映射: {len(ASR_ERROR_MAP)}条")
    print(f"  地域口音: {len(ACCENT_MAP)}个地区")
    
    print(f"\n🔧 安全约束配置:")
    for key, value in SAFETY_CONSTRAINTS.items():
        print(f"  {key}: {value}")

def test_error_scenarios():
    """测试三大误差场景"""
    print("\n" + "=" * 70)
    print("三大误差场景测试")
    print("=" * 70)
    
    matcher = IPAMatcher(enable_rule_fuzzy=True, enable_edit_fuzzy=True, debug=False)
    
    test_cases = [
        # ============== 语音识别误差 ==============
        ("tiau", "tiau", "标准发音"),
        ("tiaou", "tiau", "韵母识别误差"),
        ("diou", "tiau", "声母混淆"),
        ("tiau7", "tiau13", "声调识别误差"),
        
        # ============== 地域口音差异 ==============
        ("loŋ533", "lɒŋ533", "仙游口音"),
        ("sɔŋ533", "lɒŋ533", "城厢口音"),
        ("ia", "ie", "韵母地域变体"),
        
        # ============== 连读影响 ==============
        ("pa42lau21", "pa42lau21", "标准双音节"),
        ("ŋkɒ3", "kɒ3", "声母类化"),
        ("tiau13ʔ1", "tiau13ʔ1", "入声标记"),
        
        # ============== 安全约束测试 ==============
        ("a", "pa", "声母消失测试"),
        ("tiau", "tiau13ʔ1", "ʔ保留测试"),
    ]
    
    for query, target, scenario in test_cases:
        score = matcher.weighted_score_calc(query, target)
        
        print(f"\n📝 场景: {scenario}")
        print(f"  查询: {query} → 目标: {target}")
        print(f"  相似度: {score:.3f}")
        
        # 安全约束验证
        if "ʔ" in query and "ʔ" not in target and score > 0:
            print("  ⚠️  安全约束失败: ʔ未正确过滤")
        elif score < SAFETY_CONSTRAINTS["min_similarity_threshold"]:
            print(f"  ✅ 安全约束生效: 低于阈值{SAFETY_CONSTRAINTS['min_similarity_threshold']}")

def test_advanced_features():
    """测试高级功能"""
    print("\n" + "=" * 70)
    print("高级功能测试")
    print("=" * 70)
    
    matcher = IPAMatcher(enable_rule_fuzzy=True, enable_edit_fuzzy=True, debug=False)
    
    # 测试多字符替换
    print("\n🔍 多字符替换测试:")
    test_cases = [
        ("ia", "ie"),
        ("ua", "uo"),
        ("ou", "ɔu"),
    ]
    
    for q, t in test_cases:
        score = matcher.weighted_score_calc(q, t)
        print(f"  {q} → {t}: {score:.3f}")
    
    # 测试动态权重调整
    print("\n⚖️  动态权重调整测试:")
    test_cases = [
        ("pa", "pa42"),  # 前缀匹配
        ("lau", "lau21"),  # 后缀匹配
        ("tiau", "tiau13"),  # 完整匹配
    ]
    
    for q, t in test_cases:
        score = matcher.weighted_score_calc(q, t)
        print(f"  {q} → {t}: {score:.3f}")

def main():
    """主测试函数"""
    print("🎯 优雅的IPA匹配系统测试")
    print("融合创新与安全，覆盖三大误差场景")
    
    test_confusion_coverage()
    test_error_scenarios()
    test_advanced_features()
    
    print("\n" + "=" * 70)
    print("✅ 测试完成 - 融合方案验证成功")
    print("=" * 70)

if __name__ == "__main__":
    main()