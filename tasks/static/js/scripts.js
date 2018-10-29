var CONTENT = document.getElementById('content');

var CACHE = {
    via: function (key, callback, success) {
        if (key in CACHE) {
            return success(CACHE[key])
        }

        try {
            CACHE[key] = callback((result) => success(CACHE[key] = result))
        } catch (e) {
            console.error(e);
        }
    }
};

var ROUTES = {
    '': function () {
        MENU.setActive('home');
        API.get_list_of_task_types(function (list_of_task_types) {
            API.get_limits(function (limits) {
                CONTENT.innerHTML = TEMPLATES.home(list_of_task_types, limits);

                var main_form = document.getElementById('task_form');
                var responseDom = document.getElementById('response');
                var locker = {
                    locked: false,
                    lock: function () {
                        locker.locked = true;
                        main_form.querySelector('.pre-loader').style.display = 'block';
                    },
                    unlock: function () {
                        locker.locked = false;
                        main_form.querySelector('.pre-loader').style.display = 'none';
                    }
                };

                function paramsError(message) {
                    if (message) {
                        main_form.querySelector('.invalid-feedback').innerHTML = message;
                        main_form.querySelector('textarea[name=params]').classList.add('is-invalid');
                    } else {
                        main_form.querySelector('textarea[name=params]').classList.remove('is-invalid');
                    }
                }

                main_form.onsubmit = function (e) {
                    e.preventDefault();

                    if (locker.locked) {
                        return;
                    }

                    locker.lock();

                    try {
                        var jsonObject = FROM_PARSER.parse(e.target);

                        if (!jsonObject['email']) {
                            delete jsonObject['email'];
                        }

                        window.jsob = jsonObject;

                        if ('string' === typeof jsonObject['params']) {
                            paramsError();

                            try {
                                jsonObject['params'] = JSON.parse(jsonObject['params'])
                            } catch (e) {
                                return paramsError('Invalid json')
                            }

                            if ('object' !== typeof jsonObject['params'] || jsonObject['params'] instanceof Array) {
                                return paramsError('Params must be object or null')
                            }
                        }

                        responseDom.innerHTML = '';
                        API._.post_json('/', jsonObject, function (response) {
                            responseDom.innerHTML = TEMPLATES.run_task_response(response)
                        }, function (xhr) {
                            if (xhr.status === 400) {
                                try {
                                    var response = JSON.parse(xhr.responseText);
                                    return responseDom.innerHTML = TEMPLATES.run_task_response({
                                        'result': `<div class="alert alert-danger"><code>
                                                    <pre>${response.status}: [${response.error_code}] ${response.error_msg}</pre>
                                                    </code></div>`
                                    });
                                } catch (e) {
                                }
                            }
                            return responseDom.innerHTML = TEMPLATES.run_task_response({
                                'result': `<div class="alert alert-danger"><code>
                                                ${xhr.status}:${xhr.statusText}
                                                <pre>${xhr.responseText}</pre>
                                            </code></div>`
                            });
                        }, () => locker.unlock());

                    } catch (e) {
                        console.error(e);
                        locker.unlock()
                    }
                };

                (function () {
                    var task_name = document.getElementById('task_name');
                    var params_block = document.getElementById('params-block');
                    var defaultBlock = `<div class="form-group" id="json_form_group">
                        <label for="name">Params</label>
                        <textarea class="form-control" name="params" id="params">{}</textarea>
                        <div class="invalid-feedback"></div>
                    </div>`;
                    var dict_of_task_types = list_of_task_types.reduce(
                        function (b, task_type) {
                            b[task_type.name] = task_type;
                            return b;
                        }, {});

                    document.getElementById('task_name').onchange = function (e) {
                        var json_schema = dict_of_task_types[e.target.value].json_schema;

                        if (Object.keys(json_schema).length === 0) {
                            params_block.innerHTML = defaultBlock;
                        } else {
                            params_block.innerHTML = JSON_PARSER.parse(json_schema)('Params', 'params');
                            JSON_PARSER.initEvents(main_form);
                        }
                    };

                    var evt = document.createEvent("HTMLEvents");
                    evt.initEvent("change", false, true);
                    task_name.dispatchEvent(evt);
                })();
            })
        });
    },
    'task_types': function () {
        MENU.setActive('task_types');
        API.get_list_of_task_types(function (list_of_task_types) {
            API.get_limits(function (limit) {
                CONTENT.innerHTML = TEMPLATES.list_of_task_types(list_of_task_types, limit);
            });
        });
    },
    '404': function () {
        MENU.setActive(null);
        CONTENT.innerHTML = 'PAGE NOT FOUND';
    },
    'in_progress': function () {
        MENU.setActive('in_progress');
        API.get_in_progress(function (in_progress) {
            CONTENT.innerHTML = TEMPLATES.in_progress_list(in_progress);
        });

    },
    'completed': function (page) {
        page = parseInt(page);
        MENU.setActive('completed');
        API.get_completed(function (data) {
            CONTENT.innerHTML =
                TEMPLATES.paginator(page, data.page_count, (n) => `#completed/${n}`) +
                TEMPLATES.completed_list(data);
        }, page);
    },
};

var API = {
    _: {
        request: function (method, url, success, fail, complete) {
            var xhr = new XMLHttpRequest();
            xhr.open(method, url);
            xhr.send();
            xhr.onload = function () {
                if (200 <= xhr.status && xhr.status < 300) {
                    (success || (() => null))(xhr.responseText, xhr.status);

                } else {
                    (fail || (() => alert(xhr.status + ': ' + xhr.statusText)))(xhr);
                }
                (complete || (() => null))(xhr)
            };
        },
        get: function (url, success, fail, complete) {
            return API._.request('GET', url, success, fail, complete)
        },
        get_json: function (url, success, fail, complete) {
            return API._.get(url, (json) => success(JSON.parse(json)), fail, complete)
        },
        build_query: function (params) {
            return Object.keys(params).map(key => key + '=' + params[key]).join('&');
        },
        post_json: function (url, object, success, fail, complete) {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', url);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.send(JSON.stringify(object));
            xhr.onload = function () {
                if (200 <= xhr.status && xhr.status < 300) {
                    success(JSON.parse(xhr.responseText), xhr.status);
                } else {
                    (fail || function (x) {
                        if (x.status === 400) {
                            try {
                                var response = JSON.parse(x.responseText);

                                return alert(`${response.status}: [${response.error_code}] ${response.error_msg}`);
                            } catch (e) {
                            }
                        }
                        alert(x.status + ': ' + x.statusText);
                    })(xhr);
                }

                (complete || (() => null))(xhr)
            };
        }
    },
    get_list_of_task_types: function (success) {
        return CACHE.via('list_of_task_types', (s) => API._.get_json('/get_list_of_task_types', s), success);
    },
    get_limits: function (success) {
        return CACHE.via('limits', (s) => API._.get_json('/get_limits', s), success);
    },
    get_in_progress: function (success) {
        return API._.get_json('/get_in_progress', success);
    },
    get_completed: function (success, page) {
        return API._.get_json('/get_completed?' + API._.build_query({
            page: page || 1,
        }), success);
    },
};

var TEMPLATES = {
    _: {
        createNodes: function (str) {
            return (new DOMParser())
                .parseFromString(str.trim(), 'text/html')
                .body
                .childNodes
        },
        createNode: function (str) {
            return TEMPLATES._.createNodes(str).item(0)
        },
    },
    list_of_task_types: function (list, limits) {
        var names = limits['names'];
        return `
            <h1>Limits</h1>
            <b>Global limit: ${limits.global}</b><br>
            <br>
            <table class="table table-striped">
            <thead>
            <tr>
                <th>Name</th>
                <th>Limit</th>
            </tr>
            </thead>
            <tbody>
                ${list.reduce((base, next) => base + TEMPLATES.list_of_task_types_el(next, names[next.name] || '-'), '')}
            </tbody>
            </table>`;
    },
    list_of_task_types_el: function (element, limit) {
        return `
        <tr>
            <td>
                <a href="#task_type/${element.name}">
                    ${element.name}
                </a>
            </td>
            <td>
                ${limit} 
            </td>
        </tr>`;
    },
    header_element: function (element) {
        return `
            <a class="nav-link ${ element.active ? 'active' : ''}" href="${element.link}">
                ${element.title}
            </a>`;
    },
    in_progress_row: function (row) {
        return `
            <tr>
                <td>#${row.id}</td>
                <td>${row.name}</td>
                <td>${row.status}</td>
                <td>${row.params}</td>
                <td>${row.email || ''}</td>
                <td>${row.created_at}</td>
            </tr>`;
    },
    in_progress_list: function (rows) {
        return `
            <h1>In progress</h1>
            <br>
            <table class="table table-striped">
            <thead>
            <tr>
                <th>id</th>
                <th>name</th>
                <th>status</th>
                <th>params</th>
                <th>email</th>
                <th>created_at</th>
            </tr>
            </thead>
            <tbody>
                ${rows.reduce((b, r) => b + TEMPLATES.in_progress_row(r), '')}
            </tbody>
            </table>`;
    },
    completed_row: function (row) {
        function render_files(files) {
            if (!files) {
                return ''
            }
            return files.reduce(function (b, data) {
                return b + `<a href="${data.url}">${data.name}</a> `;
            }, '')
        }

        return `
            <tr>
                <td>#${row.id}</td>
                <td>${row.name}</td>
                <td>${row.status}</td>
                <td>${row.params}</td>
                <td>${row.email || ''}</td>
                <td>${row.result}</td>
                <td>${render_files(row.files)}</td>
                <td>${row.created_at}</td>
            </tr>`;
    },
    completed_list: function (data) {
        var rows = data.rows;
        return `
            <table class="table table-striped">
            <thead>
            <tr>
                <th>id</th>
                <th>name</th>
                <th>status</th>
                <th>params</th>
                <th>email</th>
                <th>result</th>
                <th>files</th>
                <th>created_at</th>
            </tr>
            </thead>
            <tbody>
                ${rows.reduce((b, r) => b + TEMPLATES.completed_row(r), '')}
            </tbody>
            </table>`;
    },
    paginator: function (page, count, link_generator) {
        var pages = [];
        if (page > 2) {
            pages.push({text: 1, link: link_generator(1)});
            if (page > 3) {
                pages.push({text: '...', link: null})
            }
        }
        if (page > 1) {
            pages.push({text: page - 1, link: link_generator(page - 1)});
        }

        pages.push({text: page, link: null, active: true});

        if (page < count) {
            pages.push({text: page + 1, link: link_generator(page + 1)});
        }
        if (page < count - 1) {
            if (page < count - 2) {
                pages.push({text: '...', link: null});
            }
            pages.push({text: count, link: link_generator(count)});
        }

        function renderBtn(btn) {
            var li = `<li class="page-item ${btn.active ? 'active' : ''}">`;
            if (btn.link) {
                li += `<a class="page-link" href="${btn.link}">${btn.text}</a>`
            } else {
                li += `<span class="page-link">${btn.text}</span>`
            }
            return li + "</li>"
        }

        return `
        <nav>
          <ul class="pagination justify-content-center">
          ${pages.reduce((b, p) => b + renderBtn(p), '')}
          </ul>
        </nav>`
    },
    home: function (task_types, limits) {
        function renderOption(type) {
            return `<option value="${type.name}">${type.name} ${type.name in limits ? `(${limits[type.name]})` : ''}</option>`;
        }

        return `
            <h1>Run task</h1>
            <form method="post" action="/" id="task_form">
                <div class="form-group">
                    <label for="task_name">Task name</label>
                    <select name="task_name" id="task_name" class="form-control">
                        ${task_types.reduce((b, t) => b + renderOption(t), '')}
                    </select>
                </div>
                <div class="form-group">
                    <label for="name">Email</label>
                    <input class="form-control" type="email" name="email" id="params">
                </div>
                <div id="params-block"></div>
                <div class="form-group">
                    <button type="submit" class="btn btn-success" >run</button>
                </div>
                ${TEMPLATES.preloader()}
            </form>
            <div id="response"></div>`
    },
    run_task_response(response) {
        function renderFile(f) {
            return `<a href="${f.url}" target="_blank" class="card-link">${f.name}</a>`;
        }

        return `
            <div class="card">
              <div class="card-body">
                <h5 class="card-title">Response</h5>
                <p class="card-text">${response.result}</p>
                ${(response.files || []).reduce((b, f) => b + renderFile(f), '')}
              </div>
            </div>`
    },
    preloader: function () {
        return `<div class="pre-loader"><div></div><div></div></div>`
    }
};

function router(hash) {
    if (hash === '' || hash === '#') {
        return ROUTES['']()
    }

    if (hash === '#in_progress') {
        return ROUTES["in_progress"]()
    }

    if (hash === '#task_types') {
        return ROUTES["task_types"]()
    }

    var result;

    if (result = hash.match(/^#completed(\/(\d+))?$/)) {
        return ROUTES["completed"](result[2] || 1)
    }


    return ROUTES["404"]()
}

var MENU = {
    list: {
        "home": {title: 'home', active: false, link: '#', node: null},
        "task_types": {title: 'Task types', active: false, link: '#task_types', node: null},
        "in_progress": {title: 'In progress', active: false, link: '#in_progress', node: null},
        "completed": {title: 'Completed', active: false, link: '#completed/1', node: null},
    },
    active: null,
    rootDom: document.getElementById('header'),
    init: function () {
        Object.keys(MENU.list).map(function (name) {
            MENU.rootDom.appendChild(
                MENU.list[name].node = TEMPLATES._.createNode(
                    TEMPLATES.header_element(MENU.list[name])
                )
            );
        });
    },
    setActive: function (name) {
        if (MENU.active === name) {
            return
        }
        if (MENU.active) {
            MENU.list[MENU.active].node.classList.remove('active');
            MENU.list[MENU.active].active = false;
        }
        if (name) {
            MENU.list[name].node.classList.add('active');
            MENU.list[name].active = true;
            MENU.active = name;
        }
    }
};

window.onload = function () {
    function onhashchange() {
        router(document.location.hash);
    }

    MENU.init();

    window.onhashchange = onhashchange;

    onhashchange();
};