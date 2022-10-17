const MESSAGES = {
    'en': {
        ok: 'ok',
        cancel: 'Cancel',
        lang: 'Language',
        en: 'English',
        zh: 'Chinese',
        'zh-CN': 'zh-CN',
        user: 'User',
        setting: 'setting',
        signOut: 'sing out',
        fileUploadProgress: 'File upload progress',
        scanLink: 'Scan to connect ',
        scanUsePhoneBrower: 'Please use the mobile browser to scan',
        search: 'search',
        uploadFiles: 'upload files',
        uploadDir: 'upload folder',
        newFile: 'create file',
        newDir: 'create dirctory',
        delete: 'delete',
        rename: 'rename',
        view: 'view',
        displayQRCode: 'Display QR code ',
        download: 'download',
        file: 'file',
        fileName: 'file name',
        size: 'size',
        modifyTime: 'modify time',
        operation: 'operation',
        displayHide: 'show/hide hidden files',
        root: 'roog',
        back: 'back',
        refresh: 'refresh',
        filename: 'file name',
        newFileName: 'new file name',
        pleaseInputFileName: 'please input file name',
        pleaseInput: 'please input ...',
        createNewDir: 'create new dir',
        createDirsTips: 'Use / to create multi-level directories, such as foo/bar, invalid chars: !@#$%^&*():\";\'<>?,.~.',
        diskUsage: 'disk usage',
        invalidChar: 'invalid char',
        dirNameNull: 'directory is null',
        makeSureDelete: 'Are you sure you want to delete the following files/directories?',
        accountSignIn: 'Sign In With Account',
        signIn: 'Sign In',
        username: 'username',
        password: 'password',
        pleaseInputUsername: 'please input username',
        pleaseInputPassword: 'please input password',
        authFailed: 'auth Failed',
        authSuccess: 'auth success',
        loginFailed: 'Login Failed',
        getfileContentFailed: 'get file content failed',
        fileNameCannotEmpty: 'file name can not be empty',
        getSearchHistoryFailed: 'get search history failed',
        searchFailed: 'search faild',
        uploadFailed: 'file upload failed',
        createDirSuccess: 'create directory success',
        createDirFailed: 'create directory failed',
        renameSuccess: 'rename success',
        renameFailed: 'rename failed',
        deleteSuccess: 'delete success',
        deleteFailed: 'delete failed',
        setting: 'setting',
        save: 'save',
        pbrHeight: 'progress bar height for file upload',
        showDelDirSuccess: 'show deleted info',
        nodesRefreshInterval: 'interval of refresh node info(seconds)',
        name: 'name',
        value: 'value',
        description: 'description',
        uploading: 'uploading',
        completed: 'completed',
        range: 'range',
        auth: 'Auth',
        projectUrl: 'The url of project',
        node: 'node',
        cleanupUploadCompleted: 'cleanup completed',
        zip: 'zip',
        unzip: 'unzip',
        showVerboseMessages: 'show verbose messages',
        changeDisplay: 'toggle display view',
        pleaseInputName: 'please input name',
        zipSuccess: 'zip success',
        deleteSuccess: 'delete success',
        'zh-CN': '简体中文',
        'en': 'English',
    },
    'zh-CN': {
        ok: '确定',
        cancel: '取消',
        lang: '语言',
        en: '英文',
        zh: '中文',
        'zh-CN': '简体中文',
        user: '用户',
        setting: '设置',
        signOut: '注销',
        fileUploadProgress: '文件上传进度',
        scanLink: '扫码连接',
        scanUsePhoneBrower: '打开手机浏览器扫一扫',
        search: '搜索',
        uploadFiles: '上传文件',
        uploadDir: '上传目录',
        newFile: '新建文件',
        newDir: '新建目录',
        delete: '删除',
        rename: '重命名',
        view: '预览',
        displayQRCode: '显示二维码',
        download: '下载',
        file: '文件',
        fileName: '文件名',
        size: '大小',
        modifyTime: '修改时间',
        operation: '操作',
        displayHide: '是否显示隐藏的文件',
        root: '根目录',
        back: '返回',
        refresh: '刷新',
        filename: '文件名',
        newFileName: '新文件名',
        pleaseInputFileName: '请输入新文件名',
        pleaseInput: '请输入...',
        createNewDir: '创建新目录',
        createDirsTips: '使用 / 创建多层目录，例如 foo/bar，非法字符包括： !@#$%^&*():\";\'<>?,.~。',
        diskUsage: '磁盘空间',
        invalidChar: '非法字符',
        dirNameNull: '目录不能为空',
        makeSureDelete: '确定删除以下文件/目录？',
        accountSignIn: '账号登录',
        signIn: '登录',
        username: '用户名',
        password: '密码',
        pleaseInputUsername: '请输入用户名',
        pleaseInputPassword: '请输入密码',
        authFailed: '认证失败',
        authSuccess: '认证成功',
        loginFailed: '登录失败',
        getfileContentFailed: '文件内容获取失败',
        fileNameCannotEmpty: '文件名不能为空',
        getSearchHistoryFailed: '无法获取搜索历史',
        searchFailed: '搜索失败',
        uploadFailed: '文件上传失败',
        createDirSuccess: '目录创建成功',
        createDirFailed: '目录创建失败',
        renameSuccess: '重命名成功',
        renameFailed: '重命名失败',
        deleteSuccess: '删除成功',
        deleteFailed: '删除失败',
        setting: '设置',
        save: '保存',
        pbrHeight: '文件传输进度条高度',
        showDelDirSuccess: '显示删除文件成功',
        nodesRefreshInterval: '节点信更新的间隔时间(秒)',
        name: '名字',
        value: '值',
        description: '描述',
        uploading: '上传中',
        completed: '已完成',
        range: '范围',
        auth: '作者',
        projectUrl: '项目地址',
        node: '节点',
        cleanupUploadCompleted: '清理已完成',
        zip: '压缩',
        unzip: '解压',
        showVerboseMessages: '显示更多消息',
        changeDisplay: '切换视图',
        pleaseInputName: '请输入名字',
        zipSuccess: '压缩成功',
        deleteSuccess: '删除成功',
        'zh-CN': '简体中文',
        'en': 'English',
    },
};

const I18N = new VueI18n({
    locale: navigator.language || 'zh-CN',
    messages: MESSAGES
})

function getUserSettedLang() {
    return $cookies.get('language');
}

function setDisplayLang(language) {
    if(language){
         I18N.locale = language;
         $cookies.set('language', language);
    };
}
