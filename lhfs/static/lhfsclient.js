class LHFSClient {
    constructor() {
        this.postAction = function (body, onload_callback, onerror_callback = null, uploadCallback = null) {
            var xhr = new XMLHttpRequest();
            xhr.onload = function () {
                var data = JSON.parse(xhr.responseText);
                onload_callback(xhr.status, data);
            };
            xhr.onerror = function () {
                if (onerror_callback != null) {
                    onerror_callback();
                }
            };
            xhr.open("POST", '/action', true);
            if (body.constructor.name == 'FormData') {
                xhr.upload.addEventListener('progress', function (e) {
                    if (e.lengthComputable) {
                        if (uploadCallback != null) {
                            uploadCallback(e.loaded, e.total);
                        }
                    }
                });
                xhr.send(body);
            } else {
                xhr.send(JSON.stringify({ action: body }));
            }
        };
        this._getRespData = function (xhr) {
            let contentType = xhr.getResponseHeader('content-type');
            if (contentType && contentType.indexOf('application/json') >= 0) {
                return JSON.parse(xhr.responseText);
            }
            return xhr.responseText
        }
        this.request = function (method, url, params) {
            var self = this;
            let get_params = {
                onload_callback: null,
                onerror_callback: null,
                body: null
            };
            for (var k in params) {
                get_params[k] = params[k]
            }
            var xhr = new XMLHttpRequest();
            xhr.onload = function () {
                let data = self._getRespData(xhr);
                if (params.onload_callback) {
                    get_params.onload_callback(xhr.status, data);
                }
            };
            xhr.onerror = function () {
                if (params.onerror_callback) {
                    get_params.onerror_callback(xhr.status, data);
                }
            };
            xhr.open(method, url, true);
            if (params.body) {
                console.log('params.body:')
                console.log(params.body)
                xhr.send(JSON.stringify(params.body));
            } else {
                xhr.send();
            }
        }
        this._safe_path = function (path) {
            return path.slice(0, 1) == '/' ? path : '/' + path
        }
        this._getEndpoint = function () {
            let port = window.location.port != '' ? `/${window.location.port}` : ''
            return `${window.location.protocol}//${window.location.host}${port}`
        }
        this.isNodeNull = function () {
            if (this.context == null || this.context.node == null) {
                console.error('context or context.node is null');
                return true
            }
            else {
                return false
            }
        }
        this.getFsUrl = function (dirPath) { return `/v1/fs${this._safe_path(dirPath)}` }
        this.getDownloadUrl = function (node, dirPath) { return `/v1/file/${node}${this._safe_path(dirPath)}` }

        this.fsGet = function (path, showAll = false) {
            // path like: /dir1/dir2
            let tmp_path = this._safe_path(path);
            return axios.get(`/fs${tmp_path}?showAll=${showAll}`)
        }
        this.fsCreate = function (path, params = {}) {
            let tmp_path = this._safe_path(path);
            this.post(`/fs${tmp_path}`, params);
        }
        this.fsRename = function (path, new_name, params = {}) {
            let tmp_path = this._safe_path(path);
            let req_params = params;
            req_params.body = { 'dir': { 'new_name': new_name } };
            this.put(`/fs${tmp_path}`, req_params);
        }

        this.ls = async function (node, path, showAll = false) {
            return (await this.get(`/v1/fs/${node}${this._safe_path(path)}`,
                { showAll: showAll, sort: true })).dir
        };
        this.rm = async function (node, path, force = false) {
            let safe_path = this._safe_path(path);
            return this.delete(`/v1/fs/${node}${safe_path}?force=${force}`)
        }
        this.mkdir = async function (node, path) {
            return await this.post(`/v1/fs/${node}${this._safe_path(path)}`);
        };
        this.rename = async function (node, path, new_name) {
            let safePath = this._safe_path(path);
            return await this.put(`/v1/fs/${node}${safePath}`,
                                  { 'dir': { 'new_name': new_name } })
        }
        this.cat = function (file) {
            let safe_path = this._safe_path(file);
            return axios.get(`/v1/file/${this.context.node}${safe_path}`)
        };
        this.upload = function (path, file, uploadCallback = null) {
            let formData = new FormData();
            formData.append('file', file);
            let safe_path = this._safe_path(path);
            return axios({
                url: `/v1/file/${this.context.node}${safe_path}`,
                method: 'POST',
                data: formData,
                headers: { 'Content-Type': 'multipart/form-data' },
                onUploadProgress: function (progressEvent) {
                    if (uploadCallback) {
                        uploadCallback(progressEvent)
                    }
                },
            });
        };
        this.find = function (name) {
            // find files by specified name, e.g. *.py, *.js
            return axios.post(`/v1/search/${this.context.node}`,
                { 'search': { 'partern': name } })
        };
        this.findHistory = function () {
            return axios.get(`/v1/search/${this.context.node}`);
        };
        this.auth = function (authInfo) {
            return axios.post('/auth', { auth: authInfo })
        };
        this.logout = function () {
            return axios.delete('/auth')
        };
        this.zipDirectory = async function (zipPath) {
            console.debug(`zip path: ${zipPath}`)
            return await axios.post('/action',
                                    { 'doZip': { 'path': this._safe_path(zipPath) }})
        };
        this.unzip = function (unzipPath) {
            return axios.post('/action',
                              { 'doUnzip': { 'path': this._safe_path(unzipPath) } })
        }
    }
    async get(url, params = {}) {
        let resp = await axios.get(url, { params: params });
        return resp.data
    }
    async delete(url) {
        let resp = await axios.delete(url);
        return resp.data;
    }
    async post(url, params) {
        let resp = await axios.post(url, { params: params });
        return resp.data
    }
    async put(url, data) {
        let resp = await axios.put(url, data);
        return resp.data
    }
    async listNodes() {
        return (await this.get('/nodes')).nodes;
    };
}
const FS_CLIENT =  new LHFSClient()

export { LHFSClient, FS_CLIENT };