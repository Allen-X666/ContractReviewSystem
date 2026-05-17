当前端代码有更改时，需要重新构建前端代码，执行以下命令：
```bash
npm run build
```
执行完成后，会生成 `dist` 目录，将其中的文件复制到 nginx 目录下的 `html` 目录（E:\Professional\合同审查agent\nginx-1.28.0\html）中即可。