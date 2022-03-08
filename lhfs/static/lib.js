function delItemsAfter(array, afterIndex){
    // Delete array items after <afterIndex>
    while(array.length > afterIndex + 1){
        array.pop();
    }
}

function getItemsBefore(array, beforeIndex){
    let items = [];
    if (beforeIndex >= array.length){
        items = array;
    }else{
        for (let index = 0; index <= beforeIndex; index++) {
            items.push(array[index]);
        }
    }
    return items;
}

class LoggerWithBVToast {
    // A simple logger module with vue $bvToast component
   constructor(logger, debug=false) {
       this.logger = logger;
       this._debug = debug;

       this.debug = function (msg, autoHideDelay = 1000, title = 'Debug') {
            if (this._debug == false) {return}
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
        this.warn = function (msg, autoHideDelay = 1000, title = 'Warn') {
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
    constructor(type, name, defaultVal, properties={}) {
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