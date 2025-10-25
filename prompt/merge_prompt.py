# -*- coding: utf-8 -*-

"""
Dreamheart Engine Prompt Merger (v1.0)
(基于 "Prompt 架构分析与优化报告 v4.1" 规范)

此脚本使用 lxml 库的 XInclude 功能，将已拆分的多个 XML prompt 文件
合并为一个单一的、可执行的 "Dreamheart_Engine_MERGED.xml" 文件。

功能:
1.  解析 "Dreamheart_Root.xml" 作为合并入口。
2.  自动处理所有的 "<xi:include href=... />" 标签。
3.  [关键] 自动处理 "3a/3b/3c.xml" 文件中的 <Fragment> 包装器：
    lxml 的 xinclude() 会智能地丢弃 <Fragment> 标签，
    只将其内部的子模块（例如 <EncounterSystemEngine>）注入到
    <Mechanics> 标签中，完美实现我们的“逻辑重组”。
4.  输出一个格式化、严格有效的 XML 文件。
"""

from lxml import etree
import sys
import os

# --- 配置 ---
# 主入口文件 (必须包含 xmlns:xi 命名空间)
ROOT_XML_FILE = "Dreamheart_Root.xml"

# 最终合并输出的文件名
MERGED_XML_FILE = "Dreamheart_Engine_MERGED.xml"
# ----------------

def merge_xml_files(root_file_path):
    """
    使用 lxml 的 XInclude 功能全自动合并 XML 文件。
    
    @param root_file_path: 主入口 XML 文件 (e.g., "Dreamheart_Root.xml")
    @return: 合并后的 XML 字符串，如果失败则返回 None。
    """
    try:
        # 0. 检查根文件是否存在
        if not os.path.exists(root_file_path):
            print(f"Error: 找不到根文件 '{root_file_path}'。")
            print("请确保此脚本与 'Dreamheart_Root.xml' 及其所有子文件在同一目录下运行。")
            return None

        # 1. 创建一个 XML 解析器，并启用 XInclude
        #    remove_blank_text=True 有助于生成更干净的 XML
        #    no_network=False 允许它从本地文件系统读取 (这是安全的)
        parser = etree.XMLParser(remove_blank_text=True, no_network=False)
        
        print(f"1. 正在解析主文件: {root_file_path} ...")
        
        # 2. 解析主文件，并告诉它处理所有的 xi:include
        #    这是关键一步！
        #    lxml 会在此处自动读取、解析、并注入所有 href 文件。
        #    它会自动处理 <Fragment> 包装器的“脱壳”。
        tree = etree.parse(root_file_path, parser)
        
        print("2. 正在执行 XInclude 合并 (处理 3a, 3b, 3c, ...) ...")
        tree.xinclude()
        
        print("3. 合并完成。正在生成最终的 XML 字符串...")
        
        # 3. 将合并后的树序列化为字节流 (bytes)
        #    encoding='UTF-8' 产生 UTF-8 字节流
        #    pretty_print=True 保持格式美观
        #    xml_declaration=True 包含 <?xml ...?> 头部 (现在合法了)
        merged_xml_bytes = etree.tostring(
            tree.getroot(), 
            encoding='UTF-8',  # <--- 修正点 1: 'unicode' -> 'UTF-8'
            pretty_print=True,
            xml_declaration=True
        )
        
        # 4. 将字节流解码为 Python 字符串 (str)，以便写入文件
        merged_xml_string = merged_xml_bytes.decode('utf-8') # <--- 修正点 2: 新增 decode
        
        return merged_xml_string

    except etree.XIncludeError as e:
        print(f"\n--- XINCLUDE 致命错误 ---", file=sys.stderr)
        print(f"合并失败: {e}", file=sys.stderr)
        print("这通常意味着一个子文件 (例如 3a.xml) 丢失、", file=sys.stderr)
        print("或者子文件本身存在 XML 格式错误 (例如，未转义的 '&' 或 '<')。", file=sys.stderr)
        return None
    except Exception as e:
        print(f"\n--- 发生未知错误 ---", file=sys.stderr)
        print(f"合并失败: {e}", file=sys.stderr)
        return None

# --- 主程序执行 ---
if __name__ == "__main__":
    
    print("=============================================")
    print("  Dreamheart Engine XML 合并脚本 (v4.1)")
    print("=============================================")
    
    final_prompt = merge_xml_files(ROOT_XML_FILE)
    
    if final_prompt:
        # 打印合并后大小的语句移到 try 块之前，以便在写入失败时也能看到
        print(f"\n4. 合并成功。最终 Prompt 大小:", len(final_prompt), "字符。")
        
        try:
            # 5. 示例：写入到一个文件
            with open(MERGED_XML_FILE, "w", encoding="utf-8") as f:
                f.write(final_prompt)
            print(f"5. 已保存合并后的文件到: {MERGED_XML_FILE}")
            print("\n--- 任务完成 ---")
            
        except IOError as e:
            print(f"\n--- 写入文件时发生错误 ---", file=sys.stderr)
            print(f"无法写入 {MERGED_XML_FILE}: {e}", file=sys.stderr)
    
    else:
        print("\n--- 任务失败 ---")
        print("请检查上面的错误日志。")

