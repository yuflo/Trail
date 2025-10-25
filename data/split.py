import os
from lxml import etree

# --- 配置 ---

# 源文件
SOURCE_FILE = 'dreamheart_engine_v9_7_1.xml'

# 拆分后的主文件
MAIN_FILE = 'dreamheart_main.xml'

# XInclude 命名空间
XINCLUDE_NS = "http://www.w3.org/2001/XInclude"
XI_MAP = {'xi': XINCLUDE_NS}
XI_INCLUDE = f"{{{XINCLUDE_NS}}}include"

# 一级模块定义 (根节点的直接子节点)
# 格式: '标签名': '输出文件名'
PRIMARY_MODULES = {
    'System': 'module_system.xml',
    'WorldBible': 'module_worldbible.xml',
    'Mechanics': 'module_mechanics.xml',  # 这是二级底盘
    'Execution': 'module_execution.xml',
    'ConsolidatedMemory': 'module_consolidated_memory.xml'
}

# 'Mechanics' 模块的二级拆分
# 格式: '标签名': '输出文件名'
MECHANICS_SUB_MODULES = {
    'AtomicBehaviorLibrary': 'module_mechanics_behaviors.xml',
    'CoreSystems': 'module_mechanics_coresystems.xml'
}

# --- 帮助函数 ---

def save_xml_file(element, filename):
    """
    将 lxml 元素序列化并保存到文件。
    保留 XML 声明和 UTF-8 编码。
    """
    try:
        xml_bytes = etree.tostring(
            element,
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8'
        )
        with open(filename, 'wb') as f:
            f.write(xml_bytes)
        print(f"  [成功] 已创建模块: {filename}")
    except Exception as e:
        print(f"  [失败] 创建 {filename} 时出错: {e}")

def create_mechanics_chassis(mechanics_element, chassis_filename):
    """
    特殊处理: 创建 module_mechanics.xml (二级底盘)
    它不包含完整内容，而是 XInclude 'behaviors' 和 'coresystems'
    """
    print(f"\n[处理] 正在拆分 {chassis_filename} (二级底盘)...")
    
    # 1. 创建 <Mechanics> 根节点
    mechanics_chassis_root = etree.Element(
        mechanics_element.tag, 
        nsmap=XI_MAP
    )
    
    # 2. 添加说明注释
    mechanics_chassis_root.append(etree.Comment(" " + "="*60 + " "))
    mechanics_chassis_root.append(etree.Comment(" 《Dreamheart》: 机制模块 (Mechanics Module Chassis) "))
    mechanics_chassis_root.append(etree.Comment(" 此文件是 'Mechanics' 模块的二级底盘 "))
    mechanics_chassis_root.append(etree.Comment(" 它负责组装 '行为库' 和 '核心系统' 两个子模块 "))
    mechanics_chassis_root.append(etree.Comment(" " + "="*60 + " "))
    
    # 3. 遍历 <Mechanics> 的子节点 (AtomicBehaviorLibrary 和 CoreSystems)
    for child in mechanics_element:
        # [BUG FIX v2.0] 必须显式跳过注释和非元素节点
        # lxml 中, 注释的 .tag 属性是 etree.Comment (一个函数)
        if child.tag is etree.Comment or not isinstance(child, etree._Element):
            continue

        tag = child.tag  # 现在获取 tag 是安全的

        if tag in MECHANICS_SUB_MODULES:
            sub_filename = MECHANICS_SUB_MODULES[child.tag]
            
            # 4. 保存子模块的完整内容
            save_xml_file(child, sub_filename)
            
            # 5. 在二级底盘中添加 XInclude 引用
            xi_tag = etree.Element(XI_INCLUDE, attrib={'href': sub_filename})
            mechanics_chassis_root.append(xi_tag)
        else:
            # 添加一个警告，以保持代码健壮性
            print(f"  [警告] 发现 <Mechanics> 内未知标签: <{tag}>，已跳过。")
            
    # 6. 保存二级底盘文件 (module_mechanics.xml)
    save_xml_file(mechanics_chassis_root, chassis_filename)

# --- 主函数 ---

def split_framework():
    """
    执行“一级半”拆分
    """
    print(f"--- 开始拆分 {SOURCE_FILE} ---")
    
    if not os.path.exists(SOURCE_FILE):
        print(f"[错误] 源文件未找到: {SOURCE_FILE}")
        return

    # [BUG FIX v3.0] 移除 remove_blank_text=True
    # 这个设置过于激进，它破坏了 XML 的兄弟节点结构，
    # 导致解析器只能找到第一个 <System> 元素和它后面的注释。
    # 我们现有的循环逻辑已经能正确处理空白文本节点（会跳过它们）。
    parser = etree.XMLParser(strip_cdata=False, recover=True)
    
    try:
        tree = etree.parse(SOURCE_FILE, parser)
        original_root = tree.getroot()
    except etree.XMLSyntaxError as e:
        print(f"[错误] XML 解析失败: {e}")
        return

    # 1. 创建新的主底盘根节点 (dreamheart_main.xml)
    # 复制原始根标签和属性，并添加 XInclude 命名空间
    new_main_root = etree.Element(
        original_root.tag,
        attrib=original_root.attrib,
        nsmap=XI_MAP
    )

    # 2. 捕获并复制根节点之前的所有注释 (关键的“致AI引擎”指令)
    print("[处理] 正在复制根注释...")
    node = original_root.getprevious()
    preamble_comments = []
    while node is not None:
        if isinstance(node, etree._Comment):
            preamble_comments.append(node)
        node = node.getprevious()
    
    # 将注释按原始顺序（从上到下）插入
    for comment in reversed(preamble_comments):
        new_main_root.addprevious(comment)

    # 3. 遍历原始根节点的 *所有* 直接子节点
    # 现在的 len(original_root) 会包含所有节点（元素、注释、空白文本）
    print(f"\n[处理] 正在扫描 {len(original_root)} 个一级节点...")
    for child_element in original_root:
        # [BUG FIX v2.0] 必须显式跳过注释和非元素节点
        # lxml 中, 注释的 .tag 属性是 etree.Comment (一个函数)
        if child_element.tag is etree.Comment or not isinstance(child_element, etree._Element):
            continue
            
        tag = child_element.tag  # 现在获取 tag 是安全的
        
        if tag in PRIMARY_MODULES:
            filename = PRIMARY_MODULES[tag]
            
            # 4. 特殊处理 <Mechanics>
            if tag == 'Mechanics':
                # 我们不直接保存 <Mechanics>，而是调用二级拆分函数
                # 它会创建 module_mechanics.xml (二级底盘)
                # 以及 module_mechanics_behaviors.xml 和 module_mechanics_coresystems.xml
                create_mechanics_chassis(child_element, filename)
            else:
                # 5. 标准处理 (System, WorldBible, Execution, ConsolidatedMemory)
                # 直接将完整的 XML 块保存到其模块文件
                print(f"[处理] 正在保存 {filename}...")
                save_xml_file(child_element, filename)
            
            # 6. 在主底盘中添加 XInclude 引用
            xi_tag = etree.Element(XI_INCLUDE, attrib={'href': filename})
            new_main_root.append(xi_tag)
        else:
            print(f"  [警告] 发现未知的一级标签: <{tag}>，已跳过。")

    # 7. 保存最终的主底盘文件 (dreamheart_main.xml)
    print(f"\n[处理] 正在保存主底盘文件: {MAIN_FILE}...")
    try:
        # 获取包含根注释的新树
        new_tree = new_main_root.getroottree()
        new_tree.write(
            MAIN_FILE,
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8'
        )
        print(f"  [成功] 已创建主底盘: {MAIN_FILE}")
    except Exception as e:
        print(f"  [失败] 保存 {MAIN_FILE} 时出错: {e}")

    print("\n--- 拆分完成 ---")

if __name__ == "__main__":
    split_framework()

