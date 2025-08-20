import os
import sys
import json
import time
import requests
import asyncio
import aiohttp
import aiofiles
import random
from pathlib import Path
from urllib.parse import urlparse, unquote
import logging
from typing import List, Dict, Optional, Tuple
import subprocess
import tempfile
import shutil
from config import DOUYIN_CONFIG, SERVER_CONFIG, PERFORMANCE_CONFIG, IMAGE_CONFIG

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmoticonAPI:
    def __init__(self):
        self.config = {
            'douyin_api_url': DOUYIN_CONFIG['api_url'],
            'user_agent': DOUYIN_CONFIG['user_agent'],
            'cookie': DOUYIN_CONFIG['cookie'],
            'download_dir': SERVER_CONFIG['download_dir'],
            'base_url': SERVER_CONFIG['base_url'],
            'allowed_wxids': SERVER_CONFIG['allowed_wxids'],
            'performance': PERFORMANCE_CONFIG,
            'image': IMAGE_CONFIG
        }
        Path(self.config['download_dir']).mkdir(exist_ok=True)
    
    async def process_request(self, ac: str, wxid: str, start: int = 0, limit: int = 40, keyword: str = '') -> Dict:
        """处理API请求"""
        try:
            if not ac or not wxid:
                return {'msg': '缺少必要参数', 'code': 400}
            
            if wxid not in self.config['allowed_wxids']:
                return {'msg': 'wxid不在允许列表中', 'code': 403}
            emojis = await self._call_douyin_api(ac, keyword, start, limit)

            if not emojis:
                return {'msg': '获取表情包失败', 'code': 500}
            start_time = time.time()
            converted_items = await self._download_and_convert_emojis(emojis, keyword)
            process_time = time.time() - start_time
            logger.info(f"处理完成，耗时: {process_time:.2f}秒")
            
            return {
                'msg': '请求成功',
                'code': 200,
                'items': converted_items,
                'format': 'gif',
                'original_count': len(emojis),
                'process_time': f"{process_time:.2f}s"
            }
            
        except Exception as e:
            logger.error(f"处理请求失败: {e}")
            return {'msg': f'处理失败: {str(e)}', 'code': 500}
    
    async def _call_douyin_api(self, ac: str, keyword: str, start: int, limit: int) -> List[Dict]:
        """调用抖音API获取表情包列表"""
        try:
            if start == 0:
                cursor = "0"
            else:
                cursor = str(start)
            logger.info(f"分页参数: start={start}, limit={limit}, cursor={cursor}")
            
            if start > 0 and hasattr(self, '_pagination_cache') and keyword in self._pagination_cache:
                cached_cursor = self._pagination_cache[keyword].get(str(start))
                if cached_cursor:
                    cursor = cached_cursor
                    logger.info(f"使用缓存的分页cursor: {cursor}")
            
            params = {
                "device_platform": "webapp",
                "aid": "1128",
                "keyword": keyword if ac == 'search' else "",
                "cursor": cursor,
                "msToken": self._get_ms_token()
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://www.douyin.com/",
                "Cookie": self.config['cookie']
            }
            
            logger.info(f"调用抖音API: {self.config['douyin_api_url']}")
            logger.info(f"参数: {params}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.config['douyin_api_url'],
                    params=params,
                    headers=headers,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        content_encoding = response.headers.get('content-encoding', '').lower()
                        logger.info(f"抖音API返回Content-Type: {response.headers.get('Content-Type', '')}")
                        logger.info(f"Content-Encoding: {content_encoding}")
                        
                        try:
                            data = await response.json()
                            logger.info(f"抖音API返回数据: {json.dumps(data, ensure_ascii=False)[:200]}...")
                            
                            if 'emoticon_data' in data and 'sticker_list' in data['emoticon_data']:
                                sticker_list = data['emoticon_data']['sticker_list']
                                if sticker_list:
                                    if not hasattr(self, '_pagination_cache'):
                                        self._pagination_cache = {}
                                    if keyword not in self._pagination_cache:
                                        self._pagination_cache[keyword] = {}
                                    next_cursor = data['emoticon_data'].get('next_cursor', '0')
                                    has_more = data['emoticon_data'].get('has_more', False)
                                    current_page = start // limit + 1
                                    next_page = current_page + 1
                                    next_start = next_page * limit
                                    
                                    if has_more and next_cursor:
                                        self._pagination_cache[keyword][str(next_start)] = str(next_cursor)
                                        logger.info(f"缓存分页信息: 第{next_page}页(start={next_start})使用cursor={next_cursor}")
                                    
                                    logger.info(f"成功获取 {len(sticker_list)} 个表情包，下一页cursor: {next_cursor}, 还有更多: {has_more}")
                                    return sticker_list
                                else:
                                    logger.warning("表情包列表为空")
                                    return []
                            else:
                                logger.warning(f"未找到表情包数据，完整响应: {json.dumps(data, ensure_ascii=False)[:500]}")
                                return []
                                
                        except Exception as e:
                            logger.error(f"解析抖音API响应失败: {e}")
                            try:
                                text_content = await response.text()
                                logger.error(f"原始响应内容: {text_content[:500]}")
                            except:
                                pass
                            return []
                    else:
                        logger.error(f"抖音API请求失败: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"调用抖音API失败: {e}")
            return []
    
    async def _download_and_convert_emojis(self, emojis: List[Dict], keyword: str) -> List[Dict]:
        """下载并转换表情包"""
        if not emojis:
            return []
        
        if keyword:
            folder_name = self._sanitize_filename(keyword)
        else:
            folder_name = 'home'
        folder_path = Path(self.config['download_dir']) / folder_name
        folder_path.mkdir(exist_ok=True) 
        converted_items = []
        
        for i, emoji in enumerate(emojis):
            origin_urls = emoji.get('origin', {}).get('url_list', [])
            if not origin_urls:
                continue
            original_url = origin_urls[0]
            filename = self._generate_filename(original_url)
            gif_path = folder_path / f"{filename}.gif"
            
            if gif_path.exists():
                converted_items.append({
                    'url': f"{self.config['base_url']}/{folder_path}/{filename}.gif"
                })
                continue
            
            try:
                success = await self._process_single_emoji(original_url, gif_path)
                if success:
                    converted_items.append({
                        'url': f"{self.config['base_url']}/{folder_path}/{filename}.gif"
                    })
            except Exception as e:
                logger.error(f"处理表情包失败 {i}: {e}")
        
        return converted_items
    
    async def _process_single_emoji(self, url: str, output_path: Path) -> bool:
        """处理单个表情包：下载并转换为GIF"""
        try:
            temp_file = await self._download_image(url)
            if not temp_file:
                return False
            
            try:
                success = await self._convert_to_gif(temp_file, output_path)
                return success
            finally:
                if temp_file and Path(temp_file).exists():
                    Path(temp_file).unlink()
                    
        except Exception as e:
            logger.error(f"处理表情包失败: {e}")
            return False
    
    async def _download_image(self, url: str, max_retries: int = None) -> Optional[str]:
        """完全使用curl下载图片，模拟PHP的下载方式"""
        if max_retries is None:
            max_retries = self.config['performance'].get('max_retries', 2)
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = self.config['performance'].get('retry_delay', 0.5)
                    await asyncio.sleep(delay)
                
                success = await self._download_with_curl(url)
                if success:
                    return success
                
                logger.warning(f"curl下载失败 (尝试 {attempt + 1}/{max_retries}): {url}")
                
            except Exception as e:
                logger.error(f"下载异常 (尝试 {attempt + 1}/{max_retries}): {e} - {url}")
                await asyncio.sleep(0.5)
        
        logger.error(f"下载失败，已重试 {max_retries} 次: {url}")
        return None
    
    async def _download_with_curl(self, url: str) -> Optional[str]:
        """使用系统curl命令下载，完全模拟PHP的方式"""
        try:
            temp_file = tempfile.mktemp(suffix='.tmp')
            
            cmd = [
                'curl', '-L', '-s',
                '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                '-H', 'Accept: */*',
                '-H', 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8',
                '--connect-timeout', '10',
                '--max-time', '30',
                '-o', temp_file,
                url
            ]
            
            if await self._execute_curl_cmd(cmd, temp_file):
                logger.info(f"curl下载成功: {url}")
                return temp_file
            logger.warning("标准curl参数失败，尝试激进参数")
            cmd = [
                'curl', '-L', '-s',
                '-H', 'User-Agent: curl/7.68.0',
                '-H', 'Accept: */*',
                '--connect-timeout', '15',
                '--max-time', '45',
                '--retry', '2',
                '--retry-delay', '1',
                '-o', temp_file,
                url
            ]
            
            if await self._execute_curl_cmd(cmd, temp_file):
                logger.info(f"激进curl参数下载成功: {url}")
                return temp_file
            
            logger.warning("激进curl参数失败，尝试最简参数")
            cmd = [
                'curl', '-L', '-s',
                '--connect-timeout', '20',
                '--max-time', '60',
                '-o', temp_file,
                url
            ]
            
            if await self._execute_curl_cmd(cmd, temp_file):
                logger.info(f"最简curl参数下载成功: {url}")
                return temp_file
            
            logger.error(f"所有curl参数都失败了: {url}")
            if Path(temp_file).exists():
                Path(temp_file).unlink()
            return None
                
        except Exception as e:
            logger.error(f"curl下载异常: {e}")
            return None
    
    async def _execute_curl_cmd(self, cmd: list, temp_file: str) -> bool:
        """执行curl命令的通用函数"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=70)
            
            if process.returncode == 0 and Path(temp_file).exists() and Path(temp_file).stat().st_size > 0:
                return True
            else:
                if stderr:
                    logger.debug(f"curl命令执行失败: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.debug(f"curl命令执行异常: {e}")
            return False
    
    async def _convert_to_gif(self, input_path: str, output_path: Path) -> bool:
        """转换图片为GIF，保持动图效果"""
        try:
            is_animated = await self._detect_animated_image(input_path)
            if is_animated:
                return await self._convert_animated_to_gif(input_path, output_path)
            else:
                return await self._convert_static_to_gif(input_path, output_path)
                
        except Exception as e:
            logger.error(f"转换失败: {e}")
            return False
    
    async def _detect_animated_image(self, file_path: str) -> bool:
        """检测是否为动图"""
        try:
            import imageio
            
            reader = imageio.get_reader(file_path)
            if hasattr(reader, 'length'):
                return reader.length > 1
            else:
                frames = []
                for frame in reader:
                    frames.append(frame)
                    if len(frames) > 1:
                        return True
                return False
                
        except Exception as e:
            logger.warning(f"动图检测失败，使用文件扩展名判断: {e}")
            ext = Path(file_path).suffix.lower()
            return ext in ['.gif', '.webp', '.apng']
    
    async def _convert_animated_to_gif(self, input_path: str, output_path: Path) -> bool:
        """转换动图为GIF，保持动画"""
        try:
            conversion_methods = [
                ('imageio', self._convert_with_imageio, '保持动画')
            ]
            
            for method_name, method_func, description in conversion_methods:
                try:
                    success = await method_func(input_path, output_path, animated=True)
                    
                    if success:
                        logger.info(f"{method_name}转换成功（{description}）")
                        return True
                except Exception as e:
                    logger.debug(f"{method_name}转换失败: {e}")
            
            if input_path.lower().endswith('.gif'):
                try:
                    import shutil
                    shutil.copy2(input_path, output_path)
                    logger.info("直接复制GIF文件成功")
                    return True
                except Exception as e:
                    logger.error(f"复制GIF文件失败: {e}")
            
            logger.error("所有动图转换方案都失败了")
            return False
            
        except Exception as e:
            logger.error(f"动图转换失败: {e}")
            return False
    
    async def _convert_static_to_gif(self, input_path: str, output_path: Path) -> bool:
        """转换静图为GIF"""
        try:
            conversion_methods = [
                ('Pillow', self._convert_with_pillow, '静图处理效果最好'),
                ('imageio', self._convert_with_imageio, '通用图像处理')
            ]
            
            for method_name, method_func, description in conversion_methods:
                try:
                    if method_name == 'imageio':
                        success = await method_func(input_path, output_path, animated=False)
                    else:
                        success = await method_func(input_path, output_path)
                    
                    if success:
                        logger.info(f"{method_name}转换静图成功（{description}）")
                        return True
                except ImportError:
                    if method_name == 'Pillow':
                        logger.warning("Pillow未安装")
                except Exception as e:
                    if method_name == 'Pillow':
                        logger.warning(f"{method_name}转换失败: {e}")
                    else:
                        logger.debug(f"{method_name}转换失败: {e}")
            
            logger.error("所有静图转换方案都失败了")
            return False
            
        except Exception as e:
            logger.error(f"静图转换失败: {e}")
            return False
    
    def _get_resize_dimensions(self, width: int, height: int, max_size: int = None) -> tuple:
        if max_size is None:
            max_size = self.config['image']['max_image_size']
        """计算调整后的尺寸，保持宽高比"""
        if width <= max_size and height <= max_size:
            return width, height
        
        scale = min(max_size / width, max_size / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        logger.info(f"尺寸压缩: {width}x{height} → {new_width}x{new_height}")
        return new_width, new_height
    
    def _resize_image_with_pil(self, frame, new_width: int, new_height: int):
        """使用PIL调整图片尺寸，避免重复导入"""
        try:
            import numpy as np
            from PIL import Image
            pil_img = Image.fromarray(frame)
            pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            return np.array(pil_img)
        except Exception as e:
            logger.warning(f"PIL尺寸调整失败: {e}")
            return frame

    async def _convert_with_pillow(self, input_path: str, output_path: Path) -> bool:
        """使用Pillow转换静图"""
        try:
            from PIL import Image
            
            with Image.open(input_path) as img:
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                original_width, original_height = img.size
                new_width, new_height = self._get_resize_dimensions(original_width, original_height)
                if new_width != original_width or new_height != original_height:
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                img.save(output_path, 'GIF', optimize=True)
                return True
                
        except Exception as e:
            logger.error(f"Pillow转换失败: {e}")
            return False
    
    async def _convert_with_imageio(self, input_path: str, output_path: Path, animated: bool) -> bool:
        """使用imageio转换"""
        try:
            import imageio
            import numpy as np
            
            if animated:
                reader = imageio.get_reader(input_path)
                frames = []
                for frame in reader:
                    frames.append(frame)
                
                if len(frames) > 1:
                    resized_frames = []
                    for frame in frames:
                        h, w = frame.shape[:2]
                        new_h, new_w = self._get_resize_dimensions(w, h)
                        
                        if new_h != h or new_w != w:
                            resized_frame = self._resize_image_with_pil(frame, new_w, new_h)
                        else:
                            resized_frame = frame
                        resized_frames.append(resized_frame)
                    
                    imageio.mimsave(output_path, resized_frames, format='GIF', fps=self.config['image']['gif_fps'])
                    return True
                else:
                    return await self._convert_static_to_gif(input_path, output_path)
            else:
                reader = imageio.get_reader(input_path)
                frame = reader.get_data(0)
                
                h, w = frame.shape[:2]
                new_h, new_w = self._get_resize_dimensions(w, h)
                
                if new_h != h or new_w != w:
                    frame = self._resize_image_with_pil(frame, new_w, new_h)
                
                imageio.imwrite(output_path, frame, format='GIF')
                return True
                
        except Exception as e:
            logger.error(f"imageio转换失败: {e}")
            return False
    
    def _generate_filename(self, url: str) -> str:
        """从URL生成文件名"""
        try:
            parsed = urlparse(url)
            filename = Path(parsed.path).stem
            if not filename:
                filename = f"emoji_{int(time.time())}"
            return self._sanitize_filename(filename)
        except:
            return f"emoji_{int(time.time())}"
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，确保安全"""
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename
    
    def _get_ms_token(self) -> str:
        """获取msToken，优先使用配置的，否则生成随机值"""
        if hasattr(self.config, 'ms_token') and self.config.get('ms_token'):
            return self.config['ms_token']
        import random
        import string
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(64))

def _check_global_dependencies():
    if not hasattr(_check_global_dependencies, '_checked'):
        dependencies = {
            'Pillow': 'PIL',
            'imageio': 'imageio'
        }
        
        for name, import_name in dependencies.items():
            try:
                __import__(import_name)
                logger.info(f"✅ {name}已安装")
            except ImportError:
                logger.warning(f"⚠️ {name}未安装，请运行: pip install {name}")
        
        logger.info("✅ 使用优化的转换方案（Pillow + imageio）")
        _check_global_dependencies._checked = True
_check_global_dependencies()

api = EmoticonAPI()

async def handle_request(ac: str, wxid: str, start: int = 0, limit: int = 40, keyword: str = '') -> str:
    """处理HTTP请求"""
    result = await api.process_request(ac, wxid, start, limit, keyword)
    return json.dumps(result, ensure_ascii=False, indent=2)