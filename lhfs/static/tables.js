import { NewDirDialog, RenameDialog } from "./dialogs.js";
import { LHFSClient } from "./lhfsclient.js";

export class FilesTable {
    constructor() {
        this.headers = [
            {text: '文件名', value: 'name'},
            {text: '大小', value: 'size'},
            {text: '修改时间', value: 'mtime'},
            {text: '操作', value: 'actions'},
        ];
        this.itemsPerPage = 10;
        this.search = '';
        this.items = [];
        this.selected = []
        this.extendItems = []
        this.newItemDialog = null;
        this.api = new LHFSClient();
        this.pathList = [];
        this.showAll = false;
        this.node = null;
        this.nodes = [];
        this.breadcrumbs = [];
        this.nodesInfo = {};
        this.newDirDialog = new NewDirDialog();
        this.renameDialog = new RenameDialog();
        this.diskUsage = {}
    }
    async refresh(){
        let dir = await this.api.ls(this.node, this.pathList.join('/'), this.showAll);
        this.items = dir.children;
        this.diskUsage = dir.disk_usage;
        console.debug('disk usage:', this.diskUsage.used, this.diskUsage.total)
        this.itemsPerPage = this.items.length;
        this.selected = [];
    }
    async refreshNodes() {
        var self = this;
        this.nodes_info = {};
        let nodes = await this.api.listNodes();
        nodes.forEach(item => {
            self.nodes.push(item.hostname);
            self.nodesInfo[item.hostname] = item;
            if (!self.node && item.type == 'master') {
                self.node = item.hostname;
            }
        })
    }
    async openNewDirDialog() {
        this.newDirDialog.open(this)
    }
    async newDir() {
        console.info('create new dir:', this.pathList, this.newDirDialog.name);
        this.api.mkdir(this.node, this.pathList.concat(this.newDirDialog.name).join('/'));
        console.log(I18N.t('createDirSuccess'));
        this.refresh();
        this.newDirDialog.hide()
    }
    refreshBreadcrumbs(){
        let breadcrumbs = [];
        for (let i in this.pathList) {
            breadcrumbs.push({
                text: this.pathList[i],
                disabled: false,
                index: parseInt(i),
            })
        }
        if (breadcrumbs.length >= 1) {
            breadcrumbs[breadcrumbs.length - 1].disabled = true;
        }
        this.breadcrumbs = breadcrumbs;
    }
    async clickDir(item){
        if (!item.folder){
            return;
        }
        this.pathList.push(item.name);
        this.refresh();
        this.refreshBreadcrumbs();
    }
    async goTo(item) {
        let clickIndex = parseInt(item.index);
        let pathList = this.pathList.slice(0, clickIndex + 1);
        this.pathList = pathList;
        this.refreshBreadcrumbs();
        await this.refresh();
    }
    async deleteSeleted(){
        let parDir = this.pathList.join('/');
        for (let i in this.selected) {
            let item = this.selected[i];
            let dirPath = null;
            if (item.pardir) {
                dirPath = `${item.pardir}/${item.name}`
            } else {
                dirPath = `${parDir}/${item.name}`;
            }
            await this.api.rm(this.node, dirPath, true);
            this.refresh();
        }
        this.selected = [];
    }
    getFileIcon(item) {
        if (item.folder){ return "mdi-folder"; };
        let icon = 'mdi-file';
        switch (item.type){
            case "zip": icon = "mdi-zip-box"; break;
            case "md":  icon = "mdi-language-markdown"; break;
            case "txt": icon = "mdi-note-text"; break;
            case "xlsx":
            case "xls":
                icon = "mdi-file-excel"; break;
            case "doc":
            case "docx":
                icon = "mdi-file-word"; break;
            case "ppt":
            case "pptx":
                icon = "mdi-file-powerpoint"; break;
            case "html":
            case "css":
            case "js":
            case "py":
            case "java":
            case "php":
            case "c":
            case "pyc":
                icon = 'mdi-file-code'; break;
            default:
                icon = "mdi-file"; break;
        }
        return icon;
    }
    toggleShowAll(){
        this.showAll = ! this.showAll;
        this.refresh();
    }
    getDiskUsage() {
        if (! this.diskUsage.used){
            return '0/0'
        }
        let displayUsed = humanSize(this.diskUsage.used);
        let displayTotal = humanSize(this.diskUsage.total);
        return `${displayUsed[0].toFixed(2)}${displayUsed[1]} / ${displayTotal[0].toFixed(2)}${displayTotal[1]}`;
    };
    _getDownloadUrl(item) {
        let fileDir = this.pathList.concat(item.name).join('/');
        return this.api.getDownloadUrl(this.node, item.pardir ? `${item.pardir}/${item.name}` : fileDir);
    };
    downloadFile(item){
        let link = document.createElement('a');
        link.href = this._getDownloadUrl(item);
        console.log('---->', link.href)
        link.download = item.name;
        link.click()
    };
    async zipDirectory(item) {
        console.debug(this.pathList)
        let zipPath = `${this.pathList.join('/')}/${item.name}`;
        let self = this;
        await this.api.zipDirectory(zipPath);
        self.refresh()
    };
    async openRenameDialog(item) {
        this.renameDialog.open(item);
    }
    checkNotNull(value){
        if (!value) {
            return '名字不能为空';
        }
        return true;
    }
    checkIsSame(value){
        if (!this.renameDialog.item.name == value) {
            return '请修改名字';
        }
        return true;
    }
    async renamePath() {
        if (!this.renameDialog.newName) {
            this.renameDialog.error = I18N.t('fileNameCannotEmpty');
            return;
        }
        await this.api.rename(this.node, this.pathList.concat(this.renameDialog.item.name).join('/'),
                              this.renameDialog.newName);
        console.log(I18N.t('renameSuccess'));
        this.refresh();
        this.renameDialog.hide()
    }
}
