# Llight Http File System

1. 一个基于http的轻量级文件系统，由一个master节点多个slave节点组成
1. master 和slaver节点使用rpc通信
1. 支持选择任意节点，进行文件上传、下载
1. 支持文件搜索，文件批量删除

![image](https://user-images.githubusercontent.com/16282152/157243898-e389e18b-6ff2-4a4e-a507-584fa0e7f6b7.png)

## 使用

> 安装 lhfs

git clone后，执行如命令安装

```bash
cd light-http-fs
python setup.py install
```
> 启动master节点

```bash
lhfsd
```

> 启动slave节点

修改配置，设置master节点的rpc地址：
```ini
[lhfs]
master_rpc = tcp://<MASTER HOST>:9527
```

启动 slave 节点: 
```bash
lhfsd --slave --ssh-user <root> --ssh-password <ROOT_PASSWORD>
```
*备注：ssh-user 和 ssh-password 用于节点间文件传输*
## TODO

- [X] 文件上传进度，排序未完成的置顶, 已完成的不展开(tabs)
- [X] 优化登录功能，UI优化，注销等
- [X] 支持多台节点
- [ ] 搜索框支持回车键搜索
- [ ] 支持markdown文件预览
- [ ] 支持操作记录日志


