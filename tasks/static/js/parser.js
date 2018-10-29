var JSON_PARSER = {
    SPLITTER: '--',
    templateLib: {},
    parse: function (json) {
        if ('string' === typeof json) {
            json = JSON.parse(json)
        }

        switch (json.type) {
            case 'object':
                return JSON_PARSER.parseObject(json);
            case 'array':
                return JSON_PARSER.parseArray(json);
            case 'string':
                return JSON_PARSER.parseString(json);
            case 'number':
                return JSON_PARSER.parseNumber(json, 'float');
            case 'integer':
                return JSON_PARSER.parseNumber(json, 'integer');
            case 'boolean':
                return JSON_PARSER.parseBoolean(json);
            case 'null':
                return () => (() => "");
        }
    },
    parseObject: function (json) {
        var data = {};

        Object.entries(json.properties || {}).map(function ([name, val]) {
            data[name] = {
                field: JSON_PARSER.parse(val),
                attributes: {}
            }
        });

        (json.required || []).forEach((x) => data[x].attributes['required'] = true);

        return function (group_name, prefix) {
            var inner = Object.entries(data).reduce(function (b, [title, val]) {
                var name = (null === prefix ? '' : prefix + JSON_PARSER.SPLITTER) + title;
                return b + val.field(title, name, val.attributes)
            }, '');

            return `<div class="card">
                          <div class="card-body">
                            <h4 class="card-title">${group_name}</h4>
                            <p class="card-text">${inner}</p>
                          </div>
                        </div>`;
        }
    },
    parseString: function (json) {
        return function (title, name, attrs) {
            return JSON_PARSER.renderCommonTemplate(title, name,
                `<textarea id="${name}" class="form-control" name="${name}" ${JSON_PARSER.renderAttributes(attrs)}></textarea>`)
        };
    },
    parseNumber: function (json, type) {
        return function (title, name, attrs) {
            var html_type = {
                'integer': 'number',
            }[type] || 'text';

            return JSON_PARSER.renderCommonTemplate(title, name,
                `<input id="${name}" class="form-control need-parse" data-format="${type}" type="${html_type}" name="${name}" ${JSON_PARSER.renderAttributes(attrs)}>`)
        };
    },
    parseBoolean: function (json) {
        return function (title, name, attrs) {
            return `<div class="from-group form-check">
                        <input id="${name}" class="form-check-input" type="checkbox" value="true" name="${name}" ${JSON_PARSER.renderAttributes(attrs)}>
                        <label for="${name}">${title}</label>
                    </div>`;
        };
    },
    parseArray: function (json) {
        return function (title, name, attrs) {
            var minItems = json['minItems'] || 0;

            JSON_PARSER.templateLib[name] = {
                json: json.items,
                attrs: attrs,
            };

            var default_values = '';

            for (var i = 0; i < minItems; i++) {
                default_values += JSON_PARSER.parse(json['items'])(
                    '', name + JSON_PARSER.SPLITTER + i, Object.assign(attrs, {required: true})
                )
            }

            return `
                <div class="array-block" data-name="${name}">
                    <h4>${title}[]</h4>
                    <div class="array-values">
                        ${default_values}
                    </div>
                    <br>
                    <div class="btn btn-sm btn-success array-append">+</div>
                </div>`;
        };
    },
    renderCommonTemplate(title, name, input) {
        return `<div class="from-group">
                        <label for="${name}">${title}</label>
                        ${input}
                    </div>`
    },
    renderAttributes(attrs) {
        return Object.entries(attrs || {}).reduce(function (b, [name, val]) {
            if (false === val) {
                return b
            }
            return b + ' ' + name + (val === true ? '' : `="${val}"`)
        }, '')
    },
    renderArrayValue(html) {
        return `
        <div class="array-val row">
            <div class="col-11">${html}</div>
            <div class="col-1">
                <div class="array-val-delete array-val-delete-s btn btn-sm btn-danger">-</div>
            </div>
        </div>`
    },
    initEvents(form) {
        form.querySelectorAll('.array-block').forEach(function (arrayBlock) {
            var valBlock = arrayBlock.querySelector('.array-values');
            var name = arrayBlock.getAttribute('data-name');
            arrayBlock.querySelector('.array-append').onclick = function (e) {
                e.preventDefault();
                var current_count = valBlock.children.length;
                var data = JSON_PARSER.templateLib[name];
                var inputHTML = JSON_PARSER.parse(data.json)(
                    '', name + JSON_PARSER.SPLITTER + current_count, data.attrs
                );
                valBlock.appendChild(TEMPLATES._.createNode(JSON_PARSER.renderArrayValue(inputHTML)));
                var current = valBlock.lastChild;
                current.querySelector('.array-val-delete').onclick = function (e) {
                    e.preventDefault();
                    current.remove();
                }
            };
        })
    }
};

var FROM_PARSER = {
    parse: function (form) {
        var formData = new FormData(form);
        var jsonObject = {};

        for (var [key, value]  of formData.entries()) {
            jsonObject[key] = value;
        }

        form.querySelectorAll('[type=checkbox]').forEach(function (checkbox) {
            var name = checkbox.getAttribute('name');
            jsonObject[name] = name in jsonObject;
        });

        form.querySelectorAll('.need-parse').forEach(function (checkbox) {
            var name = checkbox.getAttribute('name');
            var format = checkbox.getAttribute('data-format');
            var parsers = {
                'float': parseFloat,
                'integer': parseInt,
            };
            jsonObject[name] = (parsers[format] || ((x) => x))(jsonObject[name]);
        });

        jsonObject = FROM_PARSER.keys_split(jsonObject);

        return FROM_PARSER.resetArraysIndexes(jsonObject);
    },
    resetArraysIndexes: function (obj) {
        if (obj instanceof Array) {
            obj = Object.values(obj);
            for (var i = 0; i < obj.length; i++) {
                obj[i] = FROM_PARSER.resetArraysIndexes(obj[i])
            }
        } else if (obj instanceof Object) {
            Object.keys(obj).map(function (key) {
                obj[key] = FROM_PARSER.resetArraysIndexes(obj[key])
            });
        }
        return obj
    },
    keys_split(object) {
        function recursive_set(obj, keys, value) {
            key = keys.shift();

            if (keys.length === 0) {
                obj[key] = value;
                return
            }

            if (!(key in obj)) {
                obj[key] = !isNaN(parseInt(keys[0])) ? [] : {}
            } else {
                if ('string' === typeof obj[key]) {
                    throw Error(`Duplicated key ${key}`)
                }
            }

            recursive_set(obj[key], keys, value)
        }

        var result = {};

        for (var [key, val] of Object.entries(object)) {
            recursive_set(result, key.split(JSON_PARSER.SPLITTER), val)
        }
        return result
    }
};

