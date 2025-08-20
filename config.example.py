# 抖音API配置
DOUYIN_CONFIG = {
    'api_url': 'https://www.douyin.com/aweme/v1/web/im/resource/emoticon/search',
    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    # 重要：请替换为你的实际cookie
    # 获取方法：登录抖音网页版，按F12打开开发者工具，在Network标签页中找到任意请求，复制Cookie值
    'cookie': '你的抖音cookie在这里',
    # msToken是可选的，如果不设置会自动生成随机值
    'ms_token': None,  # 可以设置为从控制台获取的真实msToken，或保持None自动生成
}

# 服务器配置
SERVER_CONFIG = {
    'base_url': 'http://你的IP地址:8000',  # 修改为你的实际IP地址
    'download_dir': 'downloads',  # 表情包下载保存目录
    'allowed_wxids': [
        'wxid_888888',  # 添加允许访问的wxid
        'wxid_999999',
    ],
}

# 性能配置
PERFORMANCE_CONFIG = {
    'max_concurrent_downloads': 1,  # 并发下载数量
    'max_concurrent_conversions': 3,  # 并发转换数量
    'download_timeout': 30,  # 下载超时时间（秒）
    'conversion_timeout': 60,  # 转换超时时间（秒）
    'enable_parallel': True,  # 启用并行处理
    'enable_cache': True,  # 启用缓存
    'retry_delay': 0.5,  # 重试延迟（秒）
    'max_retries': 2  # 最大重试次数
}

# 图片处理配置
IMAGE_CONFIG = {
    'max_image_size': 900,  # 最大图片尺寸
    'gif_fps': 15,  # GIF帧率
    'quality': 'high'  # 图片质量
}
