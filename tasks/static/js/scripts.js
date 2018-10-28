var CONTENT = document.getElementById('content');

var CACHE = {
    via: function (key, callback, args) {
        if (key in CACHE) {
            return CACHE[key]
        }

        try {
            CACHE[key] = callback.apply(args)
        } catch (e) {
            console.error(e);
            return null;
        }
        return CACHE[key]
    }
};

var ROUTES = {
    '': function () {
        MENU.setActive('home');
        CONTENT.innerHTML = ''
    },
    'task_types': function () {
        MENU.setActive('task_types');
        CONTENT.innerHTML = TEMPLATES.list_of_task_types(
            API.get_list_of_task_types(),
            API.get_limits(),
        )
    },
    '404': function () {
        MENU.setActive(null);
        CONTENT.innerHTML = 'PAGE NOT FOUND';
    },
    'in_progress': function () {
        MENU.setActive('in_progress');
        CONTENT.innerHTML = TEMPLATES.in_progress_list(API.get_in_progress());
    },
    'completed': function (page) {
        page = parseInt(page);
        MENU.setActive('completed');
        var data = API.get_completed(page);
        CONTENT.innerHTML =
            TEMPLATES.paginator(page, data.page_count, (n) => `#completed/${n}`) +
            TEMPLATES.completed_list(data);
    },
};

var API = {
    _: {
        request: function (method, url) {
            var xhr = new XMLHttpRequest();
            xhr.open(method, url, false);
            xhr.send();
            if (xhr.status !== 200) {
                alert(xhr.status + ': ' + xhr.statusText);
                return null;
            }
            return xhr.responseText;
        },
        get: function (url) {
            return API._.request('GET', url)
        },
        get_json: function (url) {
            return JSON.parse(API._.get(url) || null)
        },
        build_query: function (params) {
            return Object.keys(params).map(key => key + '=' + params[key]).join('&');
        },
    },
    get_list_of_task_types: function () {
        return CACHE.via('list_of_task_types', () => API._.get_json('/get_list_of_task_types'));
    },
    get_limits: function () {
        return CACHE.via('limits', () => API._.get_json('/get_limits'));
    },
    get_in_progress: function () {
        return API._.get_json('/get_in_progress');
    },
    get_completed: function (page) {
        return API._.get_json('/get_completed?' + API._.build_query({
            page: page || 1,
        }));
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
            var li = `<li class="page-item ${btn.active ? 'active': ''}">`;
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