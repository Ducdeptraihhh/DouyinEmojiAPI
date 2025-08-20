# 抖音表情包API

让斗图助手使用抖音表情包API，参考文档：[斗图助手自定义接口](https://mp.weixin.qq.com/s/5fisJvX-JzF6dW6UOF3amA)

## 特性

- 自动检测动图/静图，动图保持动画，静图优化质量
- 支持WEBP、PNG、GIF等格式转换为GIF
- 自动压缩图片到900x900以内，保持宽高比
- 并发下载和转换，支持分页获取

## 安装

```bash
pip install -r requirements.txt
```

## 配置

1. 复制配置模板：`cp config.example.py config.py`
2. 编辑 `config.py`：
   - `cookie`: 抖音cookie
   - `base_url`: IP地址
   - `allowed_wxids`: wxid列表

## 启动

```bash
python3 server.py
```

服务器在 `http://你的IP:8000` 启动

## 斗图助手配置

在斗图助手自定义接口中填入：

```
http://你的IP:8000/emoticon_api
```

## 常见问题

**Q: 下载失败怎么办？**
A: 检查cookie是否过期，尝试更新cookie
B：还不行那就是我太菜写出了BUG

**Q: 转换失败怎么办？**
A: 确保已安装所有依赖库，检查图片格式是否支持
B：还不行那就是我太菜写出了BUG

**Q: 分页获取不到数据？**
A: 这是抖音API的限制，通常只能获取前几页数据
B：还不行那就是我太菜写出了BUG

**Q: 还有别的问题？**
A: 太正常了，因为我菜得抠脚，这也是第一版（屎山代码）

---

**⚠️ 免责声明**: 本工具仅用于技术研究，使用者需自行承担使用风险。
