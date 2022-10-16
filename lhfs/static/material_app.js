import { SettingsDialog } from './dialogs.js';
import { LHFSClient } from './lhfsclient.js'
import { FilesTable } from './tables.js';

new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    vuetify: new Vuetify(),
    data: {
        settingItems: [
            new SettingItem('range', 'pbarHeight', 5, { min: 1, max: 10, unit: 'px', description: 'pbrHeight' }),
            new SettingItem('switch', 'verboseMessage', false, { description: 'showVerboseMessages' }),
            new SettingItem('range', 'nodesRefreshInterval', 10, { min: 1, max: 60, description: 'nodesRefreshInterval' }),
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
        nodes_info: { null: { status: 'xx' } },
        context: { node: null },
        inited: false,
        fileSystem: new FileSystem(new LHFSClient()),
        dialog: false,
        dialogSetting: false,
        dialogNewDir: false,
        filesTable: new FilesTable(),
        settingsDialog: new SettingsDialog(),
    },
    methods: {
        // refreshChildren: function () {
        //     this.log.debug('更新目录');
        //     let node = this.nodes_info[this.context.node];
        //     if (node.status != 'active') {
        //         this.log.warn(`node ${this.fsClient.context.node} is not active`)
        //         this.fileSystem.pathItems = [];
        //         this.fileSystem.pathList = [];
        //         return;
        //     } else {
        //         this.fileSystem.refreshItems();
        //     }
        // },
        getPathText: function (pathItems) {
            let pathText = [];
            pathItems.forEach(function (item) { pathText.push(item.text) });
            return pathText;
        },
        getDirPath: function (dirItems) { return dirItems.join('/') },
        getFSPath: function (dirName) {
            return this.getDirPath(this.fileSystem.pathList.concat(dirName))
        },
        getFileIcon: function(item){
            if (item.folder){
                return "folder";
            };
            let icon = 'file-earmark';
            switch (item.type){
                case "zip": icon = "file-earmark-zip"; break;
                case "md":  icon = "language-markdown"; break;
                case "txt": icon = "sticker-text"; break;
                case "xlsx":
                case "xls":
                    icon = "file-table"; break;
                case "doc":
                case "docx":
                    icon = "file-word"; break;
                case "ppt":
                case "pptx":
                    icon = "file-powerpoint"; break;
                case "html":
                case "css":
                case "js":
                case "py":
                case "java":
                case "php":
                case "c":
                    icon = 'file-code'; break;
                case "pyc":
                    icon = 'file-code'; break;
                    default:
                    icon = "file"; break;
            }
            return icon;
        },
        goTo: function (item) {
            var self = this;
            self.showPardir = false;
            let newPathList = this.fileSystem.pathList.slice(0, clickIndex + 1);
            this.fsClient.ls(`/${newPathList.join('/')}`, self.fileSystem.showAll).then(success => {
                self.fileSystem.pathList = self.fileSystem.pathList.slice(0, clickIndex + 1);
                self.fileSystem.paths = self.fileSystem.paths.slice(0, clickIndex + 1);
                self.fileSystem.pathItems = success.data.dir.children;
                self.fileSystem.diskUsage = success.data.dir.disk_usage;
                self.fileSystem.selected.items = [];
                // self.toggleSelected()
            }).catch(error => {
                self.log.error(`请求失败，${error}`);
            });
        },
        showFileQrcode: function () {
            this.showQrcode('fileQrcode', this.fileSystem.getItemLink(this.fileSystem.selected.items[0]))
        },
        makeSureDeleteItems: function (items) {
            var self = this;
            var files = []
            let parDir = self.fileSystem.pathList.join('/');
            items.forEach(item => {
                let dirPath;
                if (item.pardir) {
                    dirPath = `${item.pardir}/${item.name}`
                } else {
                    dirPath = `${parDir}/${item.name}`;
                }
                files.push(dirPath);
            });
            this.$bvModal.msgBoxConfirm(
                this.$createElement('div', { domProps: { innerHTML: files.join('<br/>') } }),
                { title: I18N.t('makeSureDelete'), okVariant: 'danger' }
            ).then(value => {
                if (value == true) {
                    files.forEach(file => {
                        self.fileSystem.deleteDir(file).then(successs => {
                            if (self.conf.verboseMessage.current) {
                                self.log.info(I18N.t('deleteSuccess'));
                            }
                        }).catch(error => {
                            self.log.error(`${I18N.t('deleteFailed')}, ${error}`);
                        });
                    });
                    this.fileSystem.selected.items = [];
                    this.fileSystem.selected.all = false;
                    this.fileSystem.selected.indeterminate = false;
                }
            });
        },
        toggleShowAll: function () {
            this.refreshChildren();
        },
        renameDir: function () {
            if (this.renameItem.name == this.renameItem.newName) {
                return;
            }
            if (this.renameItem.newName == '') {
                this.log.error(I18N.t('fileNameCannotEmpty'));
                return;
            }
            var self = this;
            this.fileSystem.renameItemName(
                self.renameItem.name, self.renameItem.newName
            ).then(success => {
                self.log.info(I18N.t('renameSuccess'));
                self.refreshChildren();
                self.fileSystem.selected.items = [];
            }).catch(error => {
                let error_data = error.response.data;
                self.log.error(`${I18N.t('renameFailed')}, ${error_data.error}`, 5000)
            });
        },
        renameItem: function (item, newName) {
            this.fsClient.rename(self.getFSPath(item.name), newName).then(success => {
                self.log.info(I18N.t('renameSuccess'));
                self.refreshChildren();
            }).catch(error => {
                let error_data = error.response.data;
                self.log.error(`${I18N.t('renameFailed')}, ${error_data.error}`, 5000)
            });
        },
        showRenameModal: function () {
            let item = this.fileSystem.selected.items[0];
            this.renameItem = { name: item.name, newName: item.name }
        },
        uploadFiles: function (files) {
            var self = this;
            if (files.length == 0) { return };
            console.info(`准备上传 ${files.length} 个文件`);
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
        clickUploadFile: function(){
            let element = document.getElementById('inputUploadFile');
            element.click();
        },
        clickUploadDir: function(){
            let element = document.getElementById('inputUploadDir');
            element.click();
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
            self.fsClient.cat(
                self.getFSPath(item.name)
            ).then(success => {
                if (['html', 'css', 'js', 'py', 'java', 'php'].indexOf(item.type.toLocaleLowerCase()) >= 0) {
                    // use highlight js to parse code
                    self.fileEditor.mode = 'code';
                    let hljsResult = hljs.highlight(success.data, { language: item.type });
                    console.debug(hljsResult);
                    self.fileEditor.content = hljs.highlight(success.data, { language: item.type }).value;

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
        isEditable: function (item) {
            if (item.editable) {
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
        saveSettings: function () {
            this.log.warn('TODO: saving settings');
        },
        logout: function () {
            this.fsClient.logout().then(success => {
                window.location.reload();
            })
        },
        // refreshNodes: function (callback = null) {
        //     var self = this;
        //     this.fsClient.listNodes().then(success => {
        //         let nodes = [];
        //         success.data.nodes.forEach(item => {
        //             if (self.context.node == null && item.type == 'master') {
        //                 self.context.node = item.hostname;
        //             }
        //             nodes.push(item.hostname);
        //             self.nodes_info[item.hostname] = item;
        //         })
        //         self.nodes = nodes;
        //         if (callback) {
        //             callback(success.data)
        //         }
        //     })
        // },
        cleanupCompleted: function () {
            let tasks = []
            this.uploadQueue.tasks.forEach(item => {
                if (item.status != 'completed') {
                    tasks.push(tasks);
                }
                this.uploadQueue.tasks = tasks;
                this.uploadQueue.completed = 0;
            })
        },
        zipDirectory: function (item) {
            console.debug(this.fileSystem.pathList)
            let zipPath = `${this.fileSystem.pathList.join('/')}/${item.name}`;
            if (!zipPath.startsWith('/')) {
                zipPath = '/' + zipPath;
            }
            let self = this;
            this.fsClient.zipDirectory(zipPath).then(data => {
                self. refreshChildren()
            })
        },
        unzip: function (item) {
            console.debug(this.fileSystem.pathList)
            let unzipPath = `${this.fileSystem.pathList.join('/')}/${item.name}`;
            if (!unzipPath.startsWith('/')) {
                unzipPath = '/' + unzipPath;
            }
            let self = this;
            this.fsClient.unzip(unzipPath).then(data => {
                self.log.info(`unzip ${item.name} success`);
                self.refreshChildren()
            });
        },
        changeDisplayMode: function () {
            this.fileSystem.nextDisplayMode();
            this.$cookies.set('displayMode', this.fileSystem.displayMode);
        },
    },
    created: async function () {
        var self = this;
        await this.filesTable.refreshNodes();
        this.filesTable.refresh();
        this.settingItems.forEach(item => {
            self.conf[item.name] = item;
        });

        // this.fsClient.context = this.context;
        // this.fileSystem.init(this.fsClient);
        // this.fileSystem.setContext(this.context);
        // this.refreshNodes(data => {
        //     self.goTo();
        //     self.inited = true;
        // });
        // setInterval(function () {
        //     if (self.inited) {
        //         self.refreshNodes();
        //     }
        // }, self.conf.nodesRefreshInterval.current * 1000);
        setDisplayLang(getUserSettedLang() || navigator.language);
        this.fileSystem.displayMode = this.$cookies.get('displayMode') || 'table';
        this.log = new LoggerWithBVToast(this.$bvToast, false)
        this.log.debug('vue app created');
        // this.refreshConnectionLink();
    },
    mounted() {
        // let self = this;
        // this.$root.$on('bv::modal::shown', (bvEvent, modalId) => {
        //     if (modalId == 'modal-file-qrcode') {
        //         let item = self.fileSystem.selected.items[0];
        //         let filePath = this.getFSPath(item.name);
        //         self.showQrcode('fileQrcode', self.fsClient.getFSLink(filePath))
        //     }
        // })

    },
});
