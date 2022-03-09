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
        this.pathItems = [];
        this.showAll = false;
        this.displayMode = 'table';
        this.api = api;
        this.context = { node: null };
        this.selected = { all: false, indeterminate: false, items: [] };

        this.setDisplayMode = function (mode) {
            this.displayMode = mode;
        };

        this.refreshItems = function () {
            return this.changDir(this.pathList.length - 1);
        };
        this.changDir = function (index = -1) {
            var self = this;
            let newPathList = this.pathList.slice(0, index + 1);
            return this.api.ls(`/${newPathList.join('/')}`, self.showAll).then(success => {
                self.pathList = self.pathList.slice(0, index + 1);
                self.pathItems = success.data.dir.children;
                self.diskUsage = success.data.dir.disk_usage;
            });
        };
        this.deleteDir = function (dirPath) {
            var self = this;
            return this.api.rm(dirPath, true).then(successs => {
                self.refreshItems();
            });
        };
        this.setContext = function (context) {
            this.api.context = context;
        };
        this.getItemPath = function (dirName) {
            return this.pathList.concat(dirName).join('/')
        };
        this.getDownloadUrl = function (item) {
            return this.api.getDownloadUrl(item.pardir ? `${item.pardir}/${item.name}` : this.getItemPath(item.name));
        };
        this.getDiskUsage = function () {
            let displayUsed = humanSize(this.diskUsage.used);
            let displayTotal = humanSize(this.diskUsage.total);
            return `${displayUsed[0].toFixed(2)}${displayUsed[1]} / ${displayTotal[0].toFixed(2)}${displayTotal[1]}`;
        };

    }
}