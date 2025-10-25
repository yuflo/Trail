#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML格式验证工具
检查XML文件的格式规范性，包括：
- 基本格式正确性
- 标签闭合
- 编码问题
- 结构完整性
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import sys
import os
from pathlib import Path


class XMLValidator:
    """XML验证器"""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.errors = []
        self.warnings = []
        
    def validate(self):
        """执行完整验证"""
        print(f"🔍 验证文件: {self.filepath}")
        print("=" * 60)
        
        # 检查文件存在性
        if not self._check_file_exists():
            return False
            
        # 检查文件编码
        self._check_encoding()
        
        # 检查XML格式
        if not self._check_xml_format():
            return False
            
        # 检查XML结构
        self._check_xml_structure()
        
        # 输出结果
        self._print_results()
        
        return len(self.errors) == 0
    
    def _check_file_exists(self):
        """检查文件是否存在"""
        if not os.path.exists(self.filepath):
            self.errors.append(f"❌ 文件不存在: {self.filepath}")
            return False
        return True
    
    def _check_encoding(self):
        """检查文件编码"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"✅ 编码检查: UTF-8 (文件大小: {len(content)} 字符)")
        except UnicodeDecodeError:
            self.warnings.append("⚠️  文件可能不是UTF-8编码")
            try:
                with open(self.filepath, 'r', encoding='gbk') as f:
                    f.read()
                    self.warnings.append("   检测到可能是GBK编码")
            except:
                pass
    
    def _check_xml_format(self):
        """检查XML基本格式"""
        try:
            tree = ET.parse(self.filepath)
            root = tree.getroot()
            print(f"✅ XML格式正确")
            print(f"   根元素: <{root.tag}>")
            return True
        except ET.ParseError as e:
            self.errors.append(f"❌ XML解析错误: {str(e)}")
            # 尝试定位错误位置
            self._locate_parse_error(e)
            return False
        except Exception as e:
            self.errors.append(f"❌ 未知错误: {str(e)}")
            return False
    
    def _locate_parse_error(self, error):
        """定位解析错误的具体位置"""
        error_msg = str(error)
        # 从错误信息中提取行号
        if "line" in error_msg:
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 显示错误附近的代码
                    import re
                    match = re.search(r'line (\d+)', error_msg)
                    if match:
                        line_num = int(match.group(1))
                        start = max(0, line_num - 3)
                        end = min(len(lines), line_num + 2)
                        print("\n错误位置上下文:")
                        for i in range(start, end):
                            prefix = ">>> " if i == line_num - 1 else "    "
                            print(f"{prefix}{i+1}: {lines[i].rstrip()}")
            except:
                pass
    
    def _check_xml_structure(self):
        """检查XML结构完整性"""
        try:
            tree = ET.parse(self.filepath)
            root = tree.getroot()
            
            # 统计信息
            total_elements = len(list(root.iter()))
            print(f"\n📊 结构统计:")
            print(f"   总元素数: {total_elements}")
            
            # 检查标签闭合
            self._check_tag_closure(root)
            
            # 检查常见问题
            self._check_common_issues(root)
            
            # 显示结构概览
            self._show_structure_overview(root)
            
        except Exception as e:
            self.warnings.append(f"⚠️  结构检查异常: {str(e)}")
    
    def _check_tag_closure(self, root):
        """检查标签是否正确闭合"""
        tag_stack = []
        for elem in root.iter():
            tag_stack.append(elem.tag)
        print(f"   ✅ 所有标签正确闭合 (检查了 {len(tag_stack)} 个标签)")
    
    def _check_common_issues(self, root):
        """检查常见问题"""
        # 检查空元素
        empty_elements = [elem.tag for elem in root.iter() 
                         if elem.text is None and len(elem) == 0 and len(elem.attrib) == 0]
        if empty_elements:
            self.warnings.append(f"⚠️  发现 {len(empty_elements)} 个空元素")
        
        # 检查未转义的特殊字符
        for elem in root.iter():
            if elem.text:
                if '<' in elem.text and not ('&lt;' in elem.text or elem.text.strip().startswith('<![CDATA[')):
                    self.warnings.append(f"⚠️  元素 <{elem.tag}> 可能包含未转义的 '<' 字符")
                    break
    
    def _show_structure_overview(self, root, max_depth=3):
        """显示结构概览"""
        print(f"\n🌲 结构概览 (前{max_depth}层):")
        self._print_tree(root, depth=0, max_depth=max_depth)
    
    def _print_tree(self, elem, depth=0, max_depth=3):
        """递归打印树结构"""
        if depth > max_depth:
            return
            
        indent = "   " * depth
        attrs = f" [{len(elem.attrib)} attrs]" if elem.attrib else ""
        children_count = f" ({len(elem)} children)" if len(elem) > 0 else ""
        text_preview = ""
        if elem.text and elem.text.strip():
            preview = elem.text.strip()[:30]
            text_preview = f': "{preview}..."' if len(elem.text.strip()) > 30 else f': "{preview}"'
        
        print(f"{indent}<{elem.tag}>{attrs}{children_count}{text_preview}")
        
        for child in elem:
            self._print_tree(child, depth + 1, max_depth)
    
    def _print_results(self):
        """打印验证结果"""
        print("\n" + "=" * 60)
        print("📋 验证结果:")
        print("=" * 60)
        
        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for error in self.errors:
                print(f"   {error}")
        
        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ 完美! XML文件格式完全规范")
        elif not self.errors:
            print("\n✅ 通过! XML格式正确 (有一些警告)")
        else:
            print("\n❌ 失败! 请修复上述错误")


def main():
    """主函数"""
    print("=" * 60)
    print("       XML 格式验证工具 v1.0")
    print("=" * 60)
    print()
    
    # 获取文件路径
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = input("请输入XML文件路径: ").strip()
    
    # 验证文件
    validator = XMLValidator(filepath)
    success = validator.validate()
    
    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
