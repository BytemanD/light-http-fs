//use custom bootstrap styling
import {LHFSClient} from './lhfsclient.js'
// import {hljs} from 'https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.5.0/build/highlight.min.js';

new Vue({
    el: '#app',
    data: {
        settingItems: [
            new SettingItem('range', 'pbarHeight', 5, {min:1, max:10, unit: 'px', description: 'pbrHeight'}),
            new SettingItem('switch', 'verboseMessage', false, {description: 'showVerboseMessages'}),
            new SettingItem('range', 'nodesRefreshInterval', 10, {min:1, max:60, description: 'nodesRefreshInterval'}),
        ],
        // conf is a mapping parsed from settingItems
        conf: {},
        downloadFile: { name: '', qrcode: '' },
        fsClient: new LHFSClient(),
        renameItem: { name: '', newName: '' },
        newDir: { name: '', validate: null },
        fileEditor: { name: '', content: '', mode: 'text' },
        uploadQueue: { completed: 0, tasks: [] },
        debug: false,
        searchPartern: '',
        searchResult: [],
        showPardir: false,
        log: null,
        searchHistory: [],
        nodes: [],
        nodes_info: {null: {status: 'xx'}},
        context: {node: null},
        inited: false,
        fileSystem: new FileSystem(new LHFSClient()),
    },
    methods: {
        refreshChildren: function () {
            this.log.debug('更新目录');
            let node = this.nodes_info[this.context.node];
            if (node.status !='active' ){
                this.log.warn(`node ${this.fsClient.context.node} is not active`)
                this.fileSystem.pathItems = [];
                this.fileSystem.pathList = [];
                return;
            } else {
                this.fileSystem.refreshItems()
            }
        },
        clickPath: function (child) {
            if (!child.folder) { return }
            var self = this;
            let dirPath = ''
            if (child.pardir){
                dirPath = `${child.pardir}/${child.name}`;
            } else {
                dirPath = self.fileSystem.pathList.concat(child.name).join('/');
            }
            self.fsClient.ls(dirPath, self.fileSystem.showAll).then(success => {
                if (child.pardir) {
                    self.fileSystem.pathItems = [];
                    child.pardir.slice(1).split('/').forEach(item => {
                        self.fileSystem.pathItems.push(item);
                    })
                }
                self.fileSystem.pathList.push(child.name);
                self.fileSystem.pathItems = success.data.dir.children;
                self.fileSystem.diskUsage = success.data.dir.disk_usage;
                self.fileSystem.selected.items = [];
                self.toggleSelected()
            }).catch(error => {
                self.log.error(`请求失败，${error}`);
            });
        },
        getPathText: function (pathItems) {
            let pathText = [];
            pathItems.forEach(function (item) { pathText.push(item.text) });
            return pathText;
        },
        getDirPath: function (dirItems) {return dirItems.join('/')},
        getFSPath: function (dirName) {
             return this.getDirPath(this.fileSystem.pathList.concat(dirName)) 
        },

        goTo: function (clickIndex=-1) {
            var self = this;
            self.showPardir = false;
            let newPathList = this.fileSystem.pathList.slice(0, clickIndex + 1);
            this.fsClient.ls(`/${newPathList.join('/')}`, self.fileSystem.showAll).then(success => {
                self.fileSystem.pathList = self.fileSystem.pathList.slice(0, clickIndex + 1);
                self.fileSystem.pathItems = success.data.dir.children;
                self.fileSystem.diskUsage = success.data.dir.disk_usage;
                self.fileSystem.selected.items = [];
                self.toggleSelected()
            }).catch(error => {
                self.log.error(`请求失败，${error}`);
            });
        },
        setFileQrcode: function (dirItem) {
            this.downloadFile = dirItem;
        },
        showFileQrcode: function () {
            let filePath = null;
            if (this.downloadFile.pardir) {
                filePath = `${this.downloadFile.pardir}/${this.downloadFile.name}`;
            } else {
                filePath = this.getFSPath(this.downloadFile.name);
            }
            this.showQrcode('fileQrcode', this.fsClient.getFSLink(filePath))
        },
        makeSureDeleteItems: function (items) {
            var self = this;
            var files = []
            let parDir = self.fileSystem.pathList.join('/');
            items.forEach(item => {
                let dirPath;
                if (item.pardir){
                    dirPath = `${item.pardir}/${item.name}`
                } else {
                    dirPath = `${parDir}/${item.name}`;
                }
                files.push(dirPath);
            });
            this.$bvModal.msgBoxConfirm(
                this.$createElement('div', {domProps: { innerHTML: files.join('<br/>') }}),
                {title: I18N.t('makeSureDelete'), okVariant: 'danger'}
            ).then(value => {
                if (value == true) {
                    files.forEach(file => {
                        self.deleteDir(file);
                    });
                    this.fileSystem.selected.items = [];
                    this.fileSystem.selected.all = false;
                    this.fileSystem.selected.indeterminate = false;
                }
            });
        },
        deleteDir: function (dirPath) {
            var self = this;
            this.fileSystem.deleteDir(dirPath).then(successs => {
                if (self.conf.verboseMessage.current){
                    self.log.info(I18N.t('deleteSuccess'));
                }
            }).catch(error => {
                self.log.error(`${I18N.t('deleteFailed')}, ${error}`);
            });
        },
        deleteSeleted: function(){
            var deleteItems = []
            this.fileSystem.selected.items.forEach(item => {
                if(item){
                    deleteItems.push(item);
                }
            })
            if (deleteItems.length > 0){
                this.makeSureDeleteItems(deleteItems);
            }
        },
        toggleAll: function(selectAll){
            if (selectAll == true){
                this.fileSystem.selected.items = this.fileSystem.pathItems.slice();
                this.fileSystem.selected.indeterminate = false;
            } else {
                this.fileSystem.selected.items = [];
                this.fileSystem.selected.indeterminate = false;
            }
        },
        toggleSelected: function(selectedItem){
            var selectedNum = 0
            this.fileSystem.selected.items.forEach(item => {
                if(item){ selectedNum += 1; }
            })
            if (selectedNum === 0){
                this.fileSystem.selected.indeterminate = false;
                this.fileSystem.selected.all = false;
            } else if (selectedNum >= this.fileSystem.pathItems.length) {
                this.fileSystem.selected.indeterminate = false;
                this.fileSystem.selected.all = true;
            } else {
                this.fileSystem.selected.indeterminate = true;
                this.fileSystem.selected.all = false;
            }
        },
        toggleShowAll: function () {
            this.refreshChildren();
        },
        renameDir: function () {
            var self = this;
            if (self.renameItem.name == self.renameItem.newName) {
                return;
            }
            if (self.renameItem.newName == '') {
                self.log.error(I18N.t('fileNameCannotEmpty'));
                return;
            }
            this.fsClient.rename(
                self.getFSPath(self.renameItem.name), self.renameItem.newName
            ).then(success => {
                self.log.info(I18N.t('renameSuccess'));
                self.refreshChildren();
            }).catch(error => {
                let error_data = error.response.data;
                self.log.error(`${I18N.t('renameFailed')}, ${error_data.error}`, 5000)
            });
        },
        renameItem: function(item, newName){
            this.fsClient.rename(self.getFSPath(item.name), newName).then(success => {
                self.log.info(I18N.t('renameSuccess'));
                self.refreshChildren();
            }).catch(error => {
                let error_data = error.response.data;
                self.log.error(`${I18N.t('renameFailed')}, ${error_data.error}`, 5000)
            });
        },
        showRenameModal: function (item) {
            this.renameItem = { name: item.name, newName: item.name }
        },
        createDir: function () {
            var self = this;
            if (this.newDir.name == '') {
                this.log.error(I18N.t('dirNameNull'))
                return;
            }
            if (!this.newDir.validate) {
                this.log.error(I18N.t('invalidChar'))
                return;
            }
            var self = this;
            let newDir = self.getDirPath(self.fileSystem.pathList.concat(self.newDir.name));
            self.fsClient.mkdir(newDir).then(success => {
                self.log.info(I18N.t('createDirSuccess'));
                self.refreshChildren();
            }).catch(error => {
                let error_data = error.response.data;
                self.log.error(`${I18N.t('createDirFailed')}, ${error_data.error}`, 5000)
            });
        },
        uploadFiles: function (files) {
            var self = this;
            if (files.length == 0) { return };
            self.log.debug(`准备上传 ${files.length} 个文件`);
            for (let index = 0; index < files.length; index++) {
                let file = files[index];
                let progress = { file: file.name, loaded: 0, total: 100, status: 'waiting', target: this.context.node };
                self.uploadQueue.tasks.push(progress);
                self.fsClient.upload(
                    self.getPathText(self.fileSystem.pathList).join('/'), file,
                    uploadEvent => {
                        progress.loaded = uploadEvent.loaded;
                        progress.total = uploadEvent.total;
                    }
                ).then(success => {
                    self.refreshChildren()
                    self.uploadQueue.completed += 1;
                    progress.status = 'completed';
                }).catch(error => {
                    progress.status = 'failed';
                    self.log.error(`${I18N.t('uploadFailed')}, ${error}`, 5000)
                });
            }
        },
        uploadFile: function () {
            var form = document.forms["formFileUpload"];
            this.uploadFiles(form.inputUploadFile.files);
        },
        uploadDir: function () {
            var form = document.forms["formDirUpload"];
            this.uploadFiles(form.inputUploadDir.files);
        },
        showFileModal: function (item) {
            this.fileEditor.name = item.name;
            var self = this;
            console.debug(this.fileSystem.pathList);
            console.debug(item.name);
            self.fsClient.cat(
                self.getFSPath(item.name)
            ).then(success => {
                if (['html', 'css', 'js', 'py', 'java', 'php'].indexOf(item.type.toLocaleLowerCase()) >= 0){
                    // use highlight js to parse code
                    self.fileEditor.mode = 'code';
                    let hljsResult = hljs.highlight(success.data, {language: item.type});
                    console.debug(hljsResult);
                    self.fileEditor.content = hljs.highlight(success.data, {language: item.type}).value;

                } else {
                    switch (item.type.toLocaleLowerCase()) {
                        case 'md':
                            // parse markdown to html
                            self.fileEditor.mode = 'html';
                            self.fileEditor.content = marked.parse(success.data);
                            break;
                        default:
                            self.fileEditor.mode = 'text';
                            self.fileEditor.content = success.data;
                            break;
                    }
                }
            }).catch(error => {
                let msg = `${I18N.t('getfileContentFailed')}, ${error}`;
                self.log.error(msg, 5000);
            })
        },
        isEditable: function(item){
            if (item.editable){
                return true;
            }
            return ['md', 'text', 'html', 'css', 'js', 'py', 'java', 'php'].indexOf(item.type.toLocaleLowerCase()) >= 0;
        },
        updateFile: function () {
            this.log.error('文件修改功能未实现');
        },
        refreshSearchHistory: function () {
            var self = this;
            self.fsClient.findHistory().then(success => {
                self.searchHistory = success.data.search.history;
            }).catch(error => {
                self.log.error(I18N.t('getSearchHistoryFailed'));
            })
        },
        search: function () {
            if (this.searchPartern == '') { return; }
            var self = this;
            self.showPardir = true;
            self.searchResult = [];
            this.fsClient.find(this.searchPartern).then(success => {
                self.fileSystem.dirList = [];
                self.fileSystem.pathItems = success.data.search.dirs;
            }).catch(error => {
                self.log.error(`${I18N.t('searchFailed')}, ${error.status}`, 5000)
            });
        },
        showQrcode: function (elemId, text) {
            // chinese is not support for qrcode.js now
            var qrcode = new QRCode(elemId);
            qrcode.makeCode(text);
        },
        refreshConnectionLink: function () {
            this.showQrcode('connectionLink', window.location.href)
        },
        checkIsDirInvalid: function () {
            let invalidChar = this.newDir.name.search(/[!@#$%^&*():";'<>?,.~]/i);
            if (invalidChar >= 0) {
                this.newDir.validate = false;
            } else {
                this.newDir.validate = true;
            }
        },
        refreshDir: function () {
            var self = this;
            this.fsClient.ls(
                this.fileSystem.pathList.join('/'), self.fileSystem.showAll
            ).then(success => {
                self.children = success.data.dir.children;
                self.diskUsage = success.data.dir.disk_usage;
            }).catch*(error => {
                self.log.error(`请求失败,${error}`);
            });
        },
        saveSettings: function(){
            this.log.warn('TODO: saving settings');
        },
        logout: function(){
            this.fsClient.logout().then(success => {
                 window.location.reload();
            })
        },
        refreshNodes: function(callback=null){
            var self = this;
            this.fsClient.listNodes().then(success =>{
                let nodes = [];
                success.data.nodes.forEach(item => {
                    if (self.context.node == null && item.type == 'master'){
                        self.context.node = item.hostname;
                    }
                    nodes.push(item.hostname);
                    self.nodes_info[item.hostname] = item;
                })
                self.nodes = nodes;
                if (callback){
                    callback(success.data)
                }
            })
        },
        cleanupCompleted: function(){
            let tasks = []
            this.uploadQueue.tasks.forEach(item => {
                if (item.status != 'completed'){
                    tasks.push(tasks);
                }
                this.uploadQueue.tasks = tasks;
                this.uploadQueue.completed = 0;
            })
        },
        zipDirectory: function(item){
            console.log(this.fileSystem.pathList)
            let zipPath = `${this.fileSystem.pathList.join('/')}/${item.name}`;
            if(! zipPath.startsWith('/')){
                zipPath = '/'  + zipPath;
            }
            let self = this;
            this.fsClient.zipDirectory(zipPath).then(data => {
                self.refreshChildren()
            })
        },
        downloadItem: function(item){
            let link = document.createElement('a');
            link.href = this.fileSystem.getDownloadUrl(item);;
            link.download = item.name;
            link.click()
        },
        changeDisplayMode: function(mode){
            this.fileSystem.setDisplayMode(mode);
            this.$cookies.set('displayMode', mode);
        },
    },
    created: function () {
        var self = this;
        this.settingItems.forEach(item => {
            self.conf[item.name] = item;
        });
        this.fsClient.context = this.context;
        this.fileSystem.setContext(this.context);
        this.refreshNodes(data => {
            self.goTo();
            self.inited = true;
        });
        setInterval(function(){
            if (self.inited){
                self.refreshNodes();
            }
        }, self.conf.nodesRefreshInterval.current * 1000);
        setDisplayLang(getUserSettedLang() || navigator.language);
        this.changeDisplayMode(this.$cookies.get('displayMode') || 'table');
        this.log = new LoggerWithBVToast(this.$bvToast, false)
        this.log.debug('vue app created');
    },
});
