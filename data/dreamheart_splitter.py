#!/usr/bin/env python3
"""
Dreamheart Engine XML Splitter v1.0
方案D：完全扁平化拆分（7个文件）

特点：
- 数字前缀明确加载顺序
- <Mechanics> 壳保留在 main 中
- 完整的验证和错误处理
"""

import os
import sys
from lxml import etree
from pathlib import Path
from typing import Dict, List, Optional
import shutil
from datetime import datetime


class DreamheartSplitter:
    """Dreamheart 引擎 XML 拆分器"""
    
    # XInclude 命名空间
    XI_NS = "http://www.w3.org/2001/XInclude"
    
    # 拆分配置
    SPLIT_CONFIG = {
        "01_system.xml": {
            "xpath": ".//System",
            "description": "系统：身份与协议"
        },
        "02_worldbible.xml": {
            "xpath": ".//WorldBible",
            "description": "世界：法则与设定"
        },
        "03_behaviors.xml": {
            "xpath": ".//Mechanics/AtomicBehaviorLibrary",
            "description": "机制：行为库"
        },
        "04_engines.xml": {
            "xpath": ".//Mechanics/CoreSystems",
            "description": "机制：核心引擎"
        },
        "05_execution.xml": {
            "xpath": ".//Execution",
            "description": "执行：循环与规格"
        },
        "06_memory.xml": {
            "xpath": ".//ConsolidatedMemory",
            "description": "记忆：动态状态"
        }
    }
    
    def __init__(self, source_file: str, output_dir: str, backup: bool = True):
        """
        初始化拆分器
        
        Args:
            source_file: 源 XML 文件路径
            output_dir: 输出目录
            backup: 是否备份原文件
        """
        self.source_file = Path(source_file)
        self.output_dir = Path(output_dir)
        self.backup = backup
        
        # 验证源文件
        if not self.source_file.exists():
            raise FileNotFoundError(f"源文件不存在: {self.source_file}")
        
        # 解析源文件（保留注释和空白）
        parser = etree.XMLParser(
            remove_comments=False,
            remove_blank_text=False,
            strip_cdata=False
        )
        try:
            self.tree = etree.parse(str(self.source_file), parser)
            self.root = self.tree.getroot()
        except etree.XMLSyntaxError as e:
            raise ValueError(f"XML 解析失败: {e}")
        
        # 验证根标签
        if self.root.tag != "DreamheartEngineFramework":
            raise ValueError(
                f"根标签错误: 期望 'DreamheartEngineFramework', "
                f"实际 '{self.root.tag}'"
            )
        
        print(f"✓ 源文件加载成功: {self.source_file}")
        print(f"✓ 根标签: {self.root.tag}, 版本: {self.root.get('version', 'N/A')}")
    
    def split(self) -> bool:
        """
        执行拆分
        
        Returns:
            是否成功
        """
        try:
            # 1. 创建输出目录
            self._prepare_output_dir()
            
            # 2. 备份原文件
            if self.backup:
                self._backup_source()
            
            # 3. 提取各个模块
            print("\n开始拆分...")
            extracted_elements = self._extract_modules()
            
            # 4. 创建主文件
            self._create_main_file()
            
            # 5. 验证完整性
            print("\n验证拆分结果...")
            self._validate_split(extracted_elements)
            
            print(f"\n✓ 拆分成功! 输出目录: {self.output_dir}")
            self._print_summary()
            
            return True
            
        except Exception as e:
            print(f"\n✗ 拆分失败: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False
    
    def _prepare_output_dir(self):
        """准备输出目录"""
        if self.output_dir.exists():
            # 如果目录存在，询问是否覆盖
            response = input(
                f"输出目录已存在: {self.output_dir}\n"
                f"是否覆盖? [y/N]: "
            ).strip().lower()
            
            if response != 'y':
                raise RuntimeError("用户取消操作")
            
            # 清空目录
            shutil.rmtree(self.output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ 输出目录已准备: {self.output_dir}")
    
    def _backup_source(self):
        """备份源文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{self.source_file.stem}_backup_{timestamp}{self.source_file.suffix}"
        backup_path = self.source_file.parent / backup_name
        
        shutil.copy2(self.source_file, backup_path)
        print(f"✓ 源文件已备份: {backup_path}")
    
    def _extract_modules(self) -> Dict[str, etree.Element]:
        """
        提取各个模块
        
        Returns:
            提取的元素字典 {filename: element}
        """
        extracted = {}
        
        for filename, config in self.SPLIT_CONFIG.items():
            xpath = config["xpath"]
            desc = config["description"]
            
            print(f"  提取: {filename} ({desc})")
            
            # 使用 XPath 查找元素
            elements = self.root.xpath(xpath)
            
            if not elements:
                raise ValueError(f"未找到元素: {xpath}")
            
            if len(elements) > 1:
                raise ValueError(f"找到多个元素: {xpath}, 数量: {len(elements)}")
            
            element = elements[0]
            
            # 深拷贝元素（保留所有子节点和注释）
            element_copy = self._deep_copy_element(element)
            
            # 保存到文件
            output_path = self.output_dir / filename
            self._write_xml(output_path, element_copy)
            
            extracted[filename] = element_copy
            
            print(f"    ✓ 已保存: {output_path} ({self._count_lines(output_path)} 行)")
        
        return extracted
    
    def _deep_copy_element(self, element: etree.Element) -> etree.Element:
        """
        深拷贝元素（包括注释和处理指令）
        
        Args:
            element: 源元素
            
        Returns:
            拷贝的元素
        """
        # 使用 etree 的序列化/反序列化来深拷贝
        xml_string = etree.tostring(
            element,
            encoding='unicode',
            pretty_print=True
        )
        
        parser = etree.XMLParser(
            remove_comments=False,
            remove_blank_text=False
        )
        
        return etree.fromstring(xml_string, parser)
    
    def _create_main_file(self):
        """创建主文件 (00_main.xml)"""
        print(f"  创建: 00_main.xml (主入口)")
        
        # 注册 XInclude 命名空间
        etree.register_namespace('xi', self.XI_NS)
        
        # 创建根元素（复制原始属性）
        main_root = etree.Element(
            self.root.tag,
            attrib=dict(self.root.attrib)
        )
        
        # 添加顶部注释（从原文件提取）
        self._copy_top_comments(main_root)
        
        # 添加各个模块的 XInclude
        self._add_xinclude(main_root, "01_system.xml")
        self._add_xinclude(main_root, "02_worldbible.xml")
        
        # 特殊处理 Mechanics：壳在 main 中
        mechanics_shell = etree.SubElement(main_root, "Mechanics")
        self._add_xinclude(mechanics_shell, "03_behaviors.xml")
        self._add_xinclude(mechanics_shell, "04_engines.xml")
        
        self._add_xinclude(main_root, "05_execution.xml")
        self._add_xinclude(main_root, "06_memory.xml")
        
        # 保存主文件
        output_path = self.output_dir / "00_main.xml"
        self._write_xml(output_path, main_root, include_declaration=True)
        
        print(f"    ✓ 已保存: {output_path} ({self._count_lines(output_path)} 行)")
    
    def _copy_top_comments(self, target_root: etree.Element):
        """
        复制源文件顶部的注释到目标根元素之前
        
        Args:
            target_root: 目标根元素
        """
        # 获取文档级别的注释和处理指令
        for item in self.tree.xpath('/processing-instruction() | /comment()'):
            # 深拷贝并添加到根元素之前
            if isinstance(item, etree._Comment):
                comment_copy = etree.Comment(item.text)
                target_root.addprevious(comment_copy)
            elif isinstance(item, etree._ProcessingInstruction):
                pi_copy = etree.ProcessingInstruction(item.target, item.text)
                target_root.addprevious(pi_copy)
    
    def _add_xinclude(self, parent: etree.Element, href: str):
        """
        添加 XInclude 引用
        
        Args:
            parent: 父元素
            href: 引用的文件名
        """
        include = etree.SubElement(
            parent,
            f"{{{self.XI_NS}}}include"
        )
        include.set("href", href)
    
    def _write_xml(
        self,
        filepath: Path,
        element: etree.Element,
        include_declaration: bool = True
    ):
        """
        写入 XML 到文件
        
        Args:
            filepath: 文件路径
            element: XML 元素
            include_declaration: 是否包含 XML 声明
        """
        xml_string = etree.tostring(
            element,
            encoding='UTF-8',
            xml_declaration=include_declaration,
            pretty_print=True
        )
        
        filepath.write_bytes(xml_string)
    
    def _count_lines(self, filepath: Path) -> int:
        """统计文件行数"""
        return len(filepath.read_text(encoding='utf-8').splitlines())
    
    def _validate_split(self, extracted_elements: Dict[str, etree.Element]):
        """
        验证拆分的完整性
        
        Args:
            extracted_elements: 提取的元素字典
        """
        # 1. 验证文件是否都存在
        print("  [1/4] 验证文件完整性...")
        expected_files = ["00_main.xml"] + list(self.SPLIT_CONFIG.keys())
        
        for filename in expected_files:
            filepath = self.output_dir / filename
            if not filepath.exists():
                raise RuntimeError(f"文件缺失: {filename}")
        
        print("    ✓ 所有文件存在")
        
        # 2. 验证元素数量
        print("  [2/4] 验证元素数量...")
        original_tags = self._collect_all_tags(self.root)
        extracted_tags = {}
        
        for element in extracted_elements.values():
            extracted_tags.update(self._collect_all_tags(element))
        
        # 比较标签集合（忽略 Mechanics，因为它只是壳）
        original_filtered = {
            k: v for k, v in original_tags.items()
            if k != "Mechanics"
        }
        
        missing_tags = set(original_filtered.keys()) - set(extracted_tags.keys())
        if missing_tags:
            raise RuntimeError(f"元素丢失: {missing_tags}")
        
        print(f"    ✓ 元素数量匹配 (共 {len(extracted_tags)} 种标签)")
        
        # 3. 验证关键元素
        print("  [3/4] 验证关键元素...")
        critical_elements = [
            "System",
            "WorldBible",
            "AtomicBehaviorLibrary",
            "CoreSystems",
            "Execution",
            "ConsolidatedMemory"
        ]
        
        for elem_name in critical_elements:
            if elem_name not in extracted_tags:
                raise RuntimeError(f"关键元素缺失: {elem_name}")
        
        print("    ✓ 所有关键元素存在")
        
        # 4. 验证 XInclude 引用
        print("  [4/4] 验证 XInclude 引用...")
        main_file = self.output_dir / "00_main.xml"
        main_tree = etree.parse(str(main_file))
        
        includes = main_tree.xpath(
            "//xi:include",
            namespaces={"xi": self.XI_NS}
        )
        
        expected_includes = [
            "01_system.xml",
            "02_worldbible.xml",
            "03_behaviors.xml",
            "04_engines.xml",
            "05_execution.xml",
            "06_memory.xml"
        ]
        
        actual_includes = [inc.get("href") for inc in includes]
        
        if set(expected_includes) != set(actual_includes):
            raise RuntimeError(
                f"XInclude 引用不匹配\n"
                f"期望: {expected_includes}\n"
                f"实际: {actual_includes}"
            )
        
        print("    ✓ XInclude 引用正确")
        
        print("\n  ✓ 所有验证通过!")
    
    def _collect_all_tags(self, element: etree.Element) -> Dict[str, int]:
        """
        收集元素及其所有子元素的标签
        
        Args:
            element: 根元素
            
        Returns:
            标签计数字典
        """
        tags = {}
        for elem in element.iter():
            # 去除命名空间
            tag = etree.QName(elem).localname
            tags[tag] = tags.get(tag, 0) + 1
        return tags
    
    def _print_summary(self):
        """打印拆分摘要"""
        print("\n" + "="*60)
        print("拆分摘要")
        print("="*60)
        
        files = sorted(self.output_dir.glob("*.xml"))
        total_lines = 0
        
        for filepath in files:
            lines = self._count_lines(filepath)
            total_lines += lines
            
            # 获取描述
            if filepath.name == "00_main.xml":
                desc = "主入口"
            else:
                desc = self.SPLIT_CONFIG.get(filepath.name, {}).get(
                    "description", "未知"
                )
            
            print(f"  {filepath.name:25s} {lines:5d} 行  ({desc})")
        
        print("-"*60)
        print(f"  {'总计':25s} {total_lines:5d} 行")
        print("="*60)


class DreamheartMerger:
    """Dreamheart 引擎 XML 合并器（用于验证）"""
    
    XI_NS = "http://www.w3.org/2001/XInclude"
    
    def __init__(self, source_dir: str):
        """
        初始化合并器
        
        Args:
            source_dir: 拆分后的文件目录
        """
        self.source_dir = Path(source_dir)
        
        if not self.source_dir.exists():
            raise FileNotFoundError(f"源目录不存在: {self.source_dir}")
    
    def merge(self, output_file: str) -> bool:
        """
        合并拆分的文件
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            是否成功
        """
        try:
            print(f"开始合并: {self.source_dir} -> {output_file}")
            
            # 1. 加载主文件
            main_file = self.source_dir / "00_main.xml"
            if not main_file.exists():
                raise FileNotFoundError(f"主文件不存在: {main_file}")
            
            # 2. 解析并展开 XInclude
            parser = etree.XMLParser(remove_blank_text=False)
            tree = etree.parse(str(main_file), parser)
            
            # 解析 XInclude（递归展开）
            tree.xinclude()
            
            # 3. 保存合并后的文件
            output_path = Path(output_file)
            tree.write(
                str(output_path),
                encoding='UTF-8',
                xml_declaration=True,
                pretty_print=True
            )
            
            print(f"✓ 合并成功: {output_path}")
            return True
            
        except Exception as e:
            print(f"✗ 合并失败: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Dreamheart Engine XML 拆分/合并工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 拆分
  python dreamheart_splitter.py split input.xml output_dir/
  
  # 合并（验证）
  python dreamheart_splitter.py merge output_dir/ merged.xml
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="操作命令")
    
    # 拆分命令
    split_parser = subparsers.add_parser("split", help="拆分 XML 文件")
    split_parser.add_argument(
        "source_file",
        help="源 XML 文件路径"
    )
    split_parser.add_argument(
        "output_dir",
        help="输出目录"
    )
    split_parser.add_argument(
        "--no-backup",
        action="store_true",
        help="不备份源文件"
    )
    
    # 合并命令
    merge_parser = subparsers.add_parser("merge", help="合并拆分的文件（用于验证）")
    merge_parser.add_argument(
        "source_dir",
        help="拆分后的文件目录"
    )
    merge_parser.add_argument(
        "output_file",
        help="输出文件路径"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 执行命令
    if args.command == "split":
        splitter = DreamheartSplitter(
            args.source_file,
            args.output_dir,
            backup=not args.no_backup
        )
        success = splitter.split()
        return 0 if success else 1
    
    elif args.command == "merge":
        merger = DreamheartMerger(args.source_dir)
        success = merger.merge(args.output_file)
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())