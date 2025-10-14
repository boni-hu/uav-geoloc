import os
import re
from pathlib import Path
import shutil

def parse_filename(filename):
    """
    解析原始文件名，提取ID、坐标信息
    支持两种格式：
    1. JJ8TdU5_UQg_WE2qt8QbXQ,37.788169,-122.400728,.jpg
    2. satellite_37.78816344751675_-122.40075733242969.png
    """
    # 移除文件扩展名
    name_without_ext = os.path.splitext(filename)[0]
    ext = os.path.splitext(filename)[1]
    
    # 格式1: ID,lat,lon,
    pattern1 = r'^([^,]+),(-?\d+\.?\d*),(-?\d+\.?\d*),'
    match1 = re.match(pattern1, name_without_ext)
    
    if match1:
        image_id = match1.group(1)
        lat = float(match1.group(2))
        lon = float(match1.group(3))
        is_query = True  # 假设这种格式是查询图像
        return {
            'id': image_id,
            'lat': lat,
            'lon': lon,
            'is_query': is_query,
            'ext': ext
        }
    
    # 格式2: satellite_lat_lon
    pattern2 = r'^satellite_(-?\d+\.?\d*)_(-?\d+\.?\d*)$'
    match2 = re.match(pattern2, name_without_ext)
    
    if match2:
        lat = float(match2.group(1))
        lon = float(match2.group(2))
        # 使用坐标生成ID
        image_id = f"{lat}_{lon}".replace('.', '').replace('-', 'n')
        is_query = False  # 假设这种格式是预测/参考图像
        return {
            'id': image_id,
            'lat': lat,
            'lon': lon,
            'is_query': is_query,
            'ext': ext
        }
    
    return None

def generate_new_filename(info, is_success=True):
    """
    生成新的文件名
    格式: _ID_query@lat@lon@status.ext (查询图像)
    或: _ID@lat@lon@status.ext (预测图像)
    """
    query_suffix = "_query" if info['is_query'] else ""
    status = "success" if is_success else "failure"
    
    # 格式化坐标，保留6位小数
    lat_str = f"{info['lat']:.6f}"
    lon_str = f"{info['lon']:.6f}"
    
    new_name = f"_{info['id']}{query_suffix}@{lat_str}@{lon_str}@{status}{info['ext']}"
    return new_name

def rename_images_in_folder(folder_path, dry_run=True, default_status='success'):
    """
    递归重命名文件夹中的图像
    
    参数:
        folder_path: 目标文件夹路径
        dry_run: True=仅预览不实际重命名, False=执行重命名
        default_status: 默认状态 'success' 或 'failure'
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"错误: 文件夹 {folder_path} 不存在")
        return
    
    # 支持的图像格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
    
    # 统计
    total_files = 0
    renamed_files = 0
    skipped_files = 0
    
    print(f"{'=' * 80}")
    print(f"扫描文件夹: {folder}")
    print(f"模式: {'预览模式 (不会实际重命名)' if dry_run else '执行模式 (将实际重命名)'}")
    print(f"{'=' * 80}\n")
    
    # 递归遍历所有文件
    for file_path in folder.rglob('*'):
        if file_path.is_file() and file_path.suffix in image_extensions:
            total_files += 1
            
            # 解析文件名
            info = parse_filename(file_path.name)
            
            if info is None:
                print(f"⚠️  跳过 (无法解析): {file_path.name}")
                skipped_files += 1
                continue
            
            # 生成新文件名
            new_filename = generate_new_filename(info, is_success=(default_status=='success'))
            new_path = file_path.parent / new_filename
            
            # 检查新文件名是否已存在
            if new_path.exists() and new_path != file_path:
                print(f"⚠️  跳过 (目标已存在): {file_path.name}")
                skipped_files += 1
                continue
            
            # 显示重命名信息
            print(f"📁 子目录: {file_path.parent.relative_to(folder)}")
            print(f"   旧名称: {file_path.name}")
            print(f"   新名称: {new_filename}")
            print(f"   坐标: ({info['lat']}, {info['lon']})")
            print(f"   类型: {'查询图像' if info['is_query'] else '参考图像'}")
            
            # 执行重命名
            if not dry_run:
                try:
                    file_path.rename(new_path)
                    print(f"   ✅ 重命名成功\n")
                    renamed_files += 1
                except Exception as e:
                    print(f"   ❌ 重命名失败: {e}\n")
                    skipped_files += 1
            else:
                print(f"   👁️  预览模式，未实际重命名\n")
                renamed_files += 1
    
    # 输出统计
    print(f"{'=' * 80}")
    print(f"扫描完成!")
    print(f"总文件数: {total_files}")
    print(f"{'将要' if dry_run else '已'}重命名: {renamed_files}")
    print(f"跳过: {skipped_files}")
    print(f"{'=' * 80}")
    
    if dry_run and renamed_files > 0:
        print(f"\n💡 这是预览模式。如果确认无误，请设置 dry_run=False 执行实际重命名。")

# 使用示例
if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        # 执行实际重命名
        print("🚀 执行模式：将实际重命名文件\n")
        rename_images_in_folder("demo-img", dry_run=False, default_status='success')
    else:
        # 预览模式
        print("👁️  预览模式：仅显示将要进行的更改\n")
        rename_images_in_folder("demo-img", dry_run=True, default_status='success')
        print("\n" + "="*80)
        print("✅ 如果确认无误，请运行: python rename_images.py run")
        print("="*80)
