import { FS_CLIENT } from "./lhfsclient.js";

class Dialog {
    constructor() {
        this.show = false;
        this.errorMessage = null;
    }
    refreshName() {
        this.name = this.randomName();
    }
    randomName() {
        return Utils.getRandomName(this.resource);
    }
    open() {
        this.errorMessage = null;
        this.display()
    }
    display() {
        this.show = true;
    }
    hide() {
        this.show = false;
    }
    checkNotNull(value) {
        if (! value) {
            return '该选项不能为空';
        }
        return true;
    }
}
export class NewDirDialog extends Dialog {
    constructor (){
        super();
        this.name = null;
        this.path = null
    }
    open(path){
        this.path = path;
        super.open();
    }
    async commit(){
        await FS_CLIENT.mkdir(this.node, path)
    }
}
export class RenameDialog extends Dialog {
    constructor (){
        super();
        this.newName = null;
        this.item = {};
        this.error = null;
    }
    open(item){
        this.item = item;
        this.newName = this.item.name;
        // this.error = null;
        this.checkNewName();
        super.open();
    }
    checkNewName(){
        if (!this.newName){
            this.error = I18N.t('fileNameCannotEmpty');
        } else if (this.item.name == this.newName) {
            this.error = I18N.t('pleaseInputName');
        } else {
            this.error = null;
        }
    }
}

const SETTING_ITEMS = {
    pbarHeight: new SettingItem('range', 5, { min: 1, max: 10, unit: 'px', description: 'pbrHeight' }),
    verboseMessage: new SettingItem('switch', false, { description: 'showVerboseMessages' }),
    nodesRefreshInterval: new SettingItem('range', 10, { min: 1, max: 60, step: 5, description: 'nodesRefreshInterval' }),
    rowsPerPage: new SettingItem('range', 100, { min: 10, max: 100, step: 10, description: 'rowsPerPage' }),
}

export class SettingsDialog extends Dialog {
    constructor (){
        super();
        this.items = SETTING_ITEMS
    }
    saveSettings() {
        console.warn('TODO: saving settings');
    }
}
