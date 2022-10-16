function delItemsAfter(array, afterIndex) {
    // Delete array items after <afterIndex>
    while (array.length > afterIndex + 1) {
        array.pop();
    }
}

function getItemsBefore(array, beforeIndex) {
    let items = [];
    if (beforeIndex >= array.length) {
        items = array;
    } else {
        for (let index = 0; index <= beforeIndex; index++) {
            items.push(array[index]);
        }
    }
    return items;
}

let ONE_MB = 1024;
let ONE_GB = ONE_MB * 1024;


function humanSize(size) {
    let humanSize = 0;
    let unit = ''
    if (size >= ONE_GB) { humanSize = size / ONE_GB; unit = 'GB'; }
    else if (size >= ONE_MB) { humanSize = size / ONE_MB; unit = 'MB' }
    else { humanSize = size; unit = 'KB' }
    return [humanSize, unit];
}

class LoggerWithBVToast {
    // A simple logger module with vue $bvToast component
    constructor(logger, debug = false) {
        this.logger = logger;
        this._debug = debug;

        this.debug = function (msg, autoHideDelay = 1000, title = 'Debug') {
            if (this._debug == false) { return }
            this.logger.toast(msg, {
                title: title,
                variant: 'default',
                autoHideDelay: autoHideDelay
            });
        },

            this.info = function (msg, autoHideDelay = 1000, title = 'Info') {
                this.logger.toast(msg, {
                    title: title,
                    variant: 'success',
                    autoHideDelay: autoHideDelay
                });
            },
            this.warn = function (msg, autoHideDelay = 5000, title = 'Warn') {
                this.logger.toast(msg, {
                    title: title,
                    variant: 'warning',
                    autoHideDelay: autoHideDelay
                });
            },
            this.error = function (msg, autoHideDelay = 5000, level = 'Error') {
                this.logger.toast(msg, {
                    title: level,
                    variant: 'danger',
                    autoHideDelay: autoHideDelay
                });
            }
    }
}

class SettingItem {
    constructor(type, name, defaultVal, properties = {}) {
        // properties like:
        // {min: 1, max:2, description: 'help info of item'}
        this.type = type;
        this.name = name;
        this.defaultVal = defaultVal;
        this.properties = properties;
        this.current = defaultVal;

        this.min = this.properties.min || 0;
        this.max = this.properties.max || 0;
        this.unit = this.properties.unit || '';
        this.description = this.properties.description || '';
    }
}

class FileSystem {
    constructor(api) {
        this.diskUsage = { used: 0, total: 100 };
        this.pathList = [];
        this.paths = [];

        this.pathItems = [];
        this.showAll = false;
        this.displayMode = 'table';
        this.api = api;
        this.context = { node: null };
        this.selected = { all: false, indeterminate: false, items: [] };
        this.headers = ['file', 'size', 'modifyTime'];
        this.fsClient = null;

        this.init = function(fsClient){
            this.fsClient = fsClient;
        }

        this.setDisplayMode = function (mode) {
            this.displayMode = mode;
        };

        this.refreshItems = function () {
            // return this.changDir(this.pathList.length - 1);
            return this.changDir(this.items.length - 1);
        };
        this.changDir = function (index = -1) {
            var self = this;
            let newPathList = this.pathList.slice(0, index + 1);
            return this.api.ls(`/${newPathList.join('/')}`, self.showAll).then(success => {
                self.paths = self.paths.slice(0, index + 1);
                self.pathList = self.pathList.slice(0, index + 1);
                self.pathItems = success.data.dir.children;
                self.diskUsage = success.data.dir.disk_usage;
            });
        };
        this.joinPaths = function(){
            let pathString = []
            this.paths.forEach(item => {
                pathString.push(item.text)
            });
            return pathString.join('/')
        }
        this.clickChild = function(child){
            if (!child.folder) { return }
            var self = this;
            let dirPath = ''
            if (child.pardir) {
                dirPath = `${child.pardir}/${child.name}`;
            } else {
                self.paths.push({text: child.name, disabled: false, index: self.paths.length});
                dirPath = self.joinPaths();
            }
            console.log(dirPath)
            self.fsClient.ls(dirPath, self.showAll).then(success => {
                if (child.pardir) {
                    self.pathItems = [];
                    child.pardir.slice(1).split('/').forEach(item => {
                        self.pathItems.push(item);
                    })
                }
                self.pathItems = success.data.dir.children;
                console.log(self.pathItems);
                self.diskUsage = success.data.dir.disk_usage;
                self.selected.items = [];
            }).catch(error => {
                self.log.error(`请求失败，${error}`);
            });
        },
        this.clickPath = function (item) {
            var self = this;
            self.showPardir = false;
            let newPaths = this.paths.slice(0, item.index + 1);
            console.log(newPaths);

            let pathString = []
            newPaths.forEach(item => { pathString.push(item.text) });

            this.fsClient.ls(pathString.join('/'), self.showAll).then(success => {
                self.paths = newPaths;
                self.pathItems = success.data.dir.children;
                self.diskUsage = success.data.dir.disk_usage;
                self.selected.items = [];
            }).catch(error => {
                self.log.error(`请求失败，${error}`);
            });
        },
        this.deleteDir = function (dirPath) {
            var self = this;
            return this.api.rm(dirPath, true).then(successs => {
                self.refreshItems();
            });
        };
        this.setContext = function (context) {
            this.api.context = context;
        };
        this.getItemPath = function (item) {
            return this.pathList.concat(item.name).join('/')
        };
        this.getDownloadUrl = function (item) {
            return this.api.getDownloadUrl(item.pardir ? `${item.pardir}/${item.name}` : this.getItemPath(item));
        };
        this.getDiskUsage = function () {
            let displayUsed = humanSize(this.diskUsage.used);
            let displayTotal = humanSize(this.diskUsage.total);
            return `${displayUsed[0].toFixed(2)}${displayUsed[1]} / ${displayTotal[0].toFixed(2)}${displayTotal[1]}`;
        };
        this.selectOne = function(item) {
            if (this.selected.items.length == 0){
                this.selected.indeterminate = false;
                this.selected.all = false;
            } else if (this.selected.items.length == this.pathItems.length) {
                this.selected.indeterminate = false;
                this.selected.all = true;
            } else {
                this.selected.indeterminate = true;
                this.selected.all = false;
            }
        };
        this.selectAll = function(){
            if (this.selected.all) {
                this.selected.items = this.pathItems.slice();
                this.selected.indeterminate = false;
            } else {
                this.selected.items = [];
                this.selected.indeterminate = false;
            }
        };
        this.deleteSeleted = function(){
            if (this.selected.items.length == 0){
                return;
            }
            this.makeSureDeleteItems(this.selected.items);
        };
        this.nextDisplayMode = function(){
            switch (this.displayMode){
                case "table":
                    this.displayMode = 'grid'; break;
                case "grid":
                    this.displayMode = 'list'; break;
                case "list":
                    this.displayMode = 'table'; break;
                default:
                    this.displayMode = 'table'; break;
            }
        };
        this.toggleShowAll = function(){
            this.showAll = ! this.showAll;
            this.refreshItems();
        };
        this.getFileIcon = function(item){
            if (item.folder){
                return "folder-fill";
            };
            let icon = 'file-earmark-fill';
            switch (item.type){
                case "zip": icon = "file-earmark-zip-fill"; break;
                case "md":  icon = "markdown-fill"; break;
                case "txt": icon = "file-text-fill"; break;
                case "xlsx":
                case "xls":
                    icon = "file-earmark-spreadsheet-fill"; break;
                case "doc":
                case "docx":
                    icon = "file-earmark-word-fill"; break;
                case "ppt":
                case "pptx":
                    icon = "file-ppt-fill"; break;
                case "html":
                case "css":
                case "js":
                case "py":
                case "java":
                case "php":
                case "c":
                    icon = 'file-code-fill'; break;
                case "pyc":
                    icon = 'file-binary-fill'; break;
                    default:
                    icon = "file-earmark-fill"; break;
            }
            return icon;
        };
        this.downloadItem = function(item){
            let link = document.createElement('a');
            link.href = this.getDownloadUrl(item);;
            link.download = item.name;
            link.click()
        };
        this.downloadSelectedItems = function(){
            var self = this;
            this.selected.items.forEach(item => {
                self.downloadItem(item);
            })
        };
        this.getEndpoint = function(){
            let port = window.location.port != '' ? `/${window.location.port}` : ''
            return `${window.location.protocol}//${window.location.host}${port}`
        };
        this.getItemLink = function(item){
            return `${this.getEndpoint()}${this.getDownloadUrl(item)}`
        };
        this.renameItem = function(item, newName){
            return this.api.rename(this.getItemPath(item), newName)
        };
        this.renameItemName = function(itemName, newName){
            return this.api.rename(this.pathList.concat(itemName).join('/'), newName);
        }
    };
}