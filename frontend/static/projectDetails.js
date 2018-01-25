var dataText;
var glossariesNewField = [];
var blacklistsNewField = [];
var username = localStorage.getItem("username");
var password = localStorage.getItem("password");
var projectName = window.location.href.split('?')[1];
var NAV_BG_COLOR = "rgba(255, 255, 0, 0.22)";
var AUTH_HEADER = "Basic " + btoa(username + ":" + password);
var REFRESH_TLD_TABLE_INTERVAL = 10000; // 10s
var REFRESH_PIPELINE_STATUS_INTERVAL = 10000; // 10s

// function showTLDs() {
//     getDataEndPoint = mainEndPoint + "/projects/" + projectName + '/data'
//
//     $.ajax
//     ({
//         type: "GET",
//         url: mainEndPoint + "/projects/" + projectName + '/data',
//         dataType: 'json',
//         async: true,
//         headers: {
//             "Authorization": "Basic " + btoa("admin" + ":" + "123")
//         },
//         success: function (data) {
//             $(".tlds_table_body").empty();
//             $.each(data, function (index, value) {
//                 var tr = "<tr id=" + index + "_row>"
//                 tr += "<td>" + index + "</td>"
//                 tr += "<td align=\"center\">" + value + "</td>"
//                 tr += "<td align=\"center\" class=\"no_of_docs\" id=" + index + "_text_box_td\"><paper-input  required auto-validate pattern=\"[0-9]*\" maxlength=\"255\" class=\"addProjClass\" label=\"# Docs to extract\" id=" + index + "_text_box\" value=\"0\"></paper-input></td>"
//                 tr += "<td align=\"center\"><paper-button style=\"width: 120px;\" onclick=\"add_tld_to_queue(this.id);\" id=" + index + "_button raised><strong>+Add</strong></paper-button></td>"
//                 tr += "</tr>"
//                 $(".tlds_table_body").append($(tr))
//             });
//         }
//     });
// }
//
//
// function no_of_docs_from_all_change() {
//     var no_of_docs_from_all = $("#no_of_docs_from_all").val()
//     $('.tlds_table_body .no_of_docs').each(function () {
//         $(this).find(':input').val(no_of_docs_from_all)
//     });
// }
//
// function add_all_tlds_to_queue() {
//     var post_data = {"tlds": {}}
//
//     $('.tlds_table_body .no_of_docs').each(function () {
//         var index = $(this).attr('id')
//         index = index.slice(0, index.length - ("_text_box_td".length + 1));
//         var value = $(this).find(':input').val()
//         post_data["tlds"][index] = parseInt(value)
//     });
//
//     $.ajax
//     ({
//         type: "POST",
//         url: mainEndPoint + "/projects/" + projectName + '/actions/add_data',
//         dataType: 'json',
//         data: JSON.stringify(post_data),
//         async: true,
//         contentType: 'application/json; charset=utf-8',
//         processData: false,
//         headers: {
//             "Authorization": "Basic " + btoa("admin" + ":" + "123")
//         },
//         success: function (msg) {
//             console.log(msg)
//         }
//     });
// }
//
// function add_tld_to_queue(id) {
//     var post_data = {"tlds": {}}
//
//     var tld = id.slice(0, id.length - "_button".length)
//     var value = null
//     $('.tlds_table_body .no_of_docs').each(function () {
//         var index = $(this).attr('id')
//         index = index.slice(0, index.length - ("_text_box_td".length + 1));
//         if (index == tld) {
//             value = $(this).find(':input').val();
//             post_data["tlds"][index] = parseInt(value);
//         }
//
//     });
//     $.ajax
//     ({
//         type: "POST",
//         url: mainEndPoint + "/projects/" + projectName + '/actions/add_data',
//         dataType: 'json',
//         data: JSON.stringify(post_data),
//         async: true,
//         contentType: 'application/json; charset=utf-8',
//         processData: false,
//         headers: {
//             "Authorization": "Basic " + btoa("admin" + ":" + "123")
//         },
//         success: function (msg) {
//             console.log(msg)
//             alert("Added")
//         }
//     });
// }
//
//
// function updateProgress() {
//     console.log('Updating progress')
//     $.ajax
//     ({
//         type: "GET",
//         url: mainEndPoint + "/projects/" + projectName + '/actions/extract',
//         dataType: 'json',
//         async: true,
//         headers: {
//             "Authorization": "Basic " + btoa("admin" + ":" + "123")
//         },
//         success: function (res) {
//             console.log(res)
//             var res = JSON.parse(res);
//             var progress = Math.floor((res["etk_progress"]["current"] / res["etk_progress"]["total"]) * 100)
//             $('#extract_progress').attr('value', progress.toString())
//             console.log('updating progress successful')
//
//         }
//     });
//
// }


// Functions to show and hide the form elements under menu
// function handleElasticSearchForm() {
//     console.log('ES form clicked')
//     console.log(document.getElementById('elasticSearchForm').opened)
//     if (document.getElementById('elasticSearchForm').opened == true) {
//         document.getElementById('elasticSearchForm').opened = false
//     }
//     else {
//         document.getElementById('elasticSearchForm').opened = true
//     }
// }

function handleUploadFileForm() {
    console.log('Upload file form clicked')
    console.log(document.getElementById('uploadFileForm').opened)
    if (document.getElementById('uploadFileForm').opened == true) {
        document.getElementById('uploadFileForm').opened = false
    }
    else {
        document.getElementById('uploadFileForm').opened = true
    }
}

var openFile = function (event) {
    var input = event.target;
    var reader = new FileReader();
    reader.onload = function () {
        dataText = reader.result;

    };
    reader.readAsText(input.files[0]);
};

function updateFormData() {
    var glossName = document.getElementById('glossary_name').value;
    var file = document.getElementById("glossary_file").getElementsByTagName("input")[0].files[0];


    var url = backend_url + "projects/" + projectName + "/glossaries/" + glossName;
    //------------
    var formData = new FormData();

    formData.append("glossary_name", glossName);
    formData.append("glossary_file", file); // number 123456 is immediately converted to a string "123456"
    // console.log(formData);

    var request = new XMLHttpRequest();
    request.open("POST", url);
    //	request.setRequestHeader("Content-type", "application/json");
    // request.setRequestHeader("Authorization", "Basic " + btoa(username + ":" + password));

    request.onreadystatechange = function () {
        if (request.readyState === 4 && request.status === 201) {
            document.getElementById("editGlossariesDialog").toggle();
            document.getElementById("getGlossary").generateRequest();
        }
    };

    request.send(formData);

}

// function uploadSamplePagesFiles() {
//     var file = document.getElementById("samplePagesFile").getElementsByTagName("input")[0].files[0];
//
//
//     var url = backend_url + "projects/" + projectName + "/actions/upload_sample_data";
//     //------------
//     var formData = new FormData();
//
//     formData.append("data_file", file); // number 123456 is immediately converted to a string "123456"
//
//     var request = new XMLHttpRequest();
//     request.open("POST", url);
//     //	request.setRequestHeader("Content-type", "application/json");
//     request.setRequestHeader("Authorization", "Basic " + btoa(username + ":" + password));
//
//     request.onreadystatechange = function () {
//         if (request.readyState === 4 && request.status === 201) {
//             document.getElementById("uploadZipFileDialog").toggle();
//
//         }
//     };
//
//     request.send(formData);
//
// }

function submitFormData() {

    var glossName = document.getElementById('glossary_nameInput').value;
    if (/\s/.test(glossName)) {
        return;
    }
    var file = document.getElementById("glossary_fileInput").getElementsByTagName("input")[0].files[0];

    var url = backend_url + "projects/" + projectName + "/glossaries";
//------------
    var formData = new FormData();

    formData.append("glossary_name", glossName);
    formData.append("glossary_file", file); // number 123456 is immediately converted to a string "123456"
    // console.log(formData);

    var request = new XMLHttpRequest();
    request.open("POST", url);
//	request.setRequestHeader("Content-type", "application/json");
//     request.setRequestHeader("Authorization", "Basic " + btoa(username + ":" + password));

    request.onreadystatechange = function () {
        if (request.readyState === 4 && request.status === 201) {

            document.getElementById('glossary_nameInput').value = "";
            document.getElementById("addGlossaryDialog").toggle();
            document.getElementById("getGlossary").generateRequest();
        }

    };

    request.send(formData);
}

function addNewTag() {
    var xhr = new XMLHttpRequest();
    var url = backend_url + "projects/" + projectName + "/tags";
    var name = document.getElementById("tagNameInput").value;
    if (/\s/.test(name)) {
        return;
    }
    var description = document.getElementById("tagDescriptionInput").value;
    var screenlabel = document.getElementById("tagSceenLabelInput").value;
    var positiveprecision = document.getElementById("tagPositiveInput").value;
    var negativeprecision = document.getElementById("tagNegativeInput").value;
    var inmenu = document.getElementById("tagCheckBoxInput").checked;

    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-type", "application/json");
    // xhr.setRequestHeader("Authorization", "Basic " + btoa(username + ":" + password));

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 201) {
            document.getElementById("addTagsDialog").toggle();
            document.getElementById("getTags").generateRequest();
            document.getElementById("tagNameInput").value = "";
            document.getElementById("tagDescriptionInput").value = "";
            document.getElementById("tagSceenLabelInput").value = "";
            document.getElementById("tagPositiveInput").value = "";
            document.getElementById("tagNegativeInput").value = ""
            document.getElementById("tagCheckBoxInput").checked = false;


        }
    };

    var data = JSON.stringify({
        "tag_name": name + "",
        "tag_object": {
            "description": description + "",
            "include_in_menu": inmenu,
            "name": name + "",
            "negative_class_precision": parseFloat(negativeprecision),
            "positive_class_precision": parseFloat(positiveprecision),
            "screen_label": screenlabel
        }
    });

    xhr.send(data);

}

function addNewTableValue() {
    var xhr = new XMLHttpRequest();
    var url = backend_url + "projects/" + projectName + "/table_attributes";
    var fieldName = document.getElementById("fieldInputDropDownInput").selectedItem.value;
    var attribute = document.getElementById("tableAttributeInputValue").value;
    var values = (document.getElementById("textAreaForTableAttribute").value).split("\n");

    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-type", "application/json");
    // xhr.setRequestHeader("Authorization", "Basic " + btoa(username + ":" + password));

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 201) {
            AddNewTableAttributeDialog.toggle();
            document.getElementById("fieldInputDropDownInput").selected = "0";
            document.getElementById("tableAttributeInputValue").value = "";
            document.getElementById("textAreaForTableAttribute").value = "";
            document.getElementById("tableAttributes").generateRequest();

        }
    }
    var data = JSON.stringify({
        "field_name": fieldName,
        "info": {},
        "name": attribute,
        "value": values
    });
    xhr.send(data);

}

function addNewField() {
    var xhr = new XMLHttpRequest();
    var url = backend_url + "projects/" + projectName + "/fields";
    var name = document.getElementById("fieldnameinput").value;
    if (/\s/.test(name)) {
        return;
    }
    var description = document.getElementById("fielddescriptioninput").value;
    var screenlabel = document.getElementById("fieldscreenlabelinput").value;
    var screen_label_plural = document.getElementById("fieldscreenlabelPluralinput").value;
    if (screenlabel == "") screenlabel = name;
    if (screen_label_plural == "") screen_label_plural = screenlabel;


    var color = document.getElementById("fieldcolorinput").value;
    var type = document.getElementById("fieldtypeinput").selectedItem.value;
    var predefinedExtractor = "";
    if (document.getElementById("fieldpredefinedExtractor").selectedItem) {
        predefinedExtractor = document.getElementById("fieldpredefinedExtractor").selectedItem.value;
    }

    var groupname = document.getElementById("fieldgroupnameinput").value;
    var icon = document.getElementById("fieldiconinput").value;
    var searchimp = parseInt(document.getElementById("fieldsearchinput").selectedItem.value);
    var ruleExtractor = document.getElementById("fieldRuleExtractor").checked;
    var combinefields = document.getElementById("fieldcombinedfieldsinput").checked;
    var facet = document.getElementById("fieldfacetinput").checked;
    var link = document.getElementById("fieldlinkinput").selectedItem.value;
    var result = document.getElementById("fieldresultinput").selectedItem.value;
    var search = document.getElementById("fieldsearchinput2").checked;
    var networksearch = document.getElementById("fieldnetworkinput").checked;
    var ruleextractTarget = document.getElementById("fieldRuleExtractorTarget").selectedItem.value;
    var caseSense = document.getElementById("getCaseSenstive").checked;
    var groupOrder = parseInt(document.getElementById("groupOrderInput").value);
    var fieldOrder = parseInt(document.getElementById("fieldOrderInput").value);
    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-type", "application/json");
    // xhr.setRequestHeader("Authorization", "Basic " + btoa(username + ":" + password));

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 201) {
            addFieldDialog.toggle();
            document.getElementById("getFields").generateRequest();
            glossariesNewField = [];
            blacklistsNewField = [];
            document.getElementById("fieldnameinput").value = "";
            document.getElementById("fielddescriptioninput").value = "";
            document.getElementById("fieldscreenlabelinput").value = "";
            document.getElementById("fieldscreenlabelPluralinput").value = "";
            document.getElementById("fieldcolorinput").value = "amber";
            document.getElementById("getCaseSenstive").checked = "";


            document.getElementById("fieldgroupnameinput").value = "";
            document.getElementById("fieldiconinput").value = "icons:default";
            document.getElementById("fieldsearchinput").selected = "0";
            document.getElementById("fieldtypeinput").selected = "0";
            document.getElementById("fieldRuleExtractor").checked = false;
            document.getElementById("fieldpredefinedExtractor").selected = "0";

            document.getElementById("fieldcombinedfieldsinput").checked = false;
            document.getElementById("fieldfacetinput").checked = false;
            document.getElementById("fieldlinkinput").selected = "0";
            document.getElementById("fieldresultinput").selected = "0";
            document.getElementById("fieldsearchinput2").checked = false;
            document.getElementById("fieldnetworkinput").checked = false;
            document.getElementById("fieldRuleExtractorTarget").selected = "2";

            document.getElementById("groupOrderInput").value = "";
            document.getElementById("fieldOrderInput").value = "";

        }
    };

    var data = JSON.stringify({
        "field_name": name,
        "field_object": {
            "color": color,
            "case_sensitive": caseSense,
            "combine_fields": combinefields,
            "description": description,
            "glossaries": glossariesNewField,
            "blacklists": blacklistsNewField,
            "group_name": groupname,
            "icon": icon,
            "name": name,
            "screen_label": screenlabel,
            "screen_label_plural": screen_label_plural,
            "search_importance": searchimp,
            "show_as_link": link,
            "show_in_facets": facet,
            "show_in_result": result,
            "show_in_search": search,
            "type": type,
            "use_in_network_search": networksearch,
            "rule_extractor_enabled": ruleExtractor,
            "predefined_extractor": predefinedExtractor,
            "rule_extraction_target": ruleextractTarget,
            "group_order": groupOrder,
            "field_order": fieldOrder
        }
    });

    xhr.send(data);

}

function setDefaultIcon() {
    document.getElementById("iconField").value = "icons:default";
}

function setDefaultColor() {
    document.getElementById("colorField").value = "amber";
}

function addDefaultIcon() {
    document.getElementById("fieldiconinput").value = "icons:default";
}

function addDefaultColor() {
    document.getElementById("fieldcolorinput").value = "amber";
}

poly = Polymer({
    is: 'project-details',

    ready: function () {
        this.fields = [];
        this.tags = [];
        this.glossaryFormField = [];
        this.glossaries = [];
        this.fieldFormGlossaries = [];
        this.fieldFormBlacklists = [];
        this.tagsData = [];
        this.fieldsData = [];
        this.tableAttributes = [];
        this.fieldNames = [];
        this.etkStatus = false;

        this.$.projectNameHeader.textContent = "Project: " + projectName;

        this.updateDone(); // update all tabs
        this.navAction();
        this.refreshPipelineStatus(true);
        this.refreshTldTable(true);
        this.tldTableData = [];
        // this.$.tldTable.sort = this.sortCaseInsensitive;

        $(document).on('tap', '.btnAddToLandmark', this.addToLandmark);
        $(document).on('tap', '.btnDeleteFileData', this.deleteFileData);

        this.colorSet = {
            "#ffb300": "amber",
            "#1e88e5": "blue",
            "#546e7a": "blue-grey",
            "#6d4c41": "brown",
            "#00acc1": "cyan",
            "#f4511e": "deep-orange",
            "#5e35b1": "deep-purple",
            "#43a047": "green",
            "#1b5e20": "green",
            "#757575": "grey",
            "#3949ab": "indigo",
            "#039be5": "light-blue",
            "#7cb342": "light-green",
            "#c0ca33": "lime",
            "#fb8c00": "orange",
            "#d81b60": "pink",
            "#8e24aa": "purple",
            "#e53935": "red",
            "#00897b": "teal",
            "#fdd835": "yellow",
            "#b71c1c": "dark-red"
        };

        this.searchImportance = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"];
        this.show_as_linkArray = ["text", "entity"];
        this.show_in_resultArray = ["header", "detail", "description", "no", "title", "nested"];
        this.type = ["string", "date", "email", "hyphenated", "location", "image", "phone", "username", "kg_id", "number"];
        this.predefined_extractor_Array = ["none", "address", "country", "email", "posting_date", "phone", "review_id", "social_media", "TLD"];
        this.extractionTargetArray = ["title_only", "description_only", "title_and_description"];
    },
    _getColor: function () {
        if (this.$$('#colorSelect').color == undefined) return "amber";
        this.$$('#fieldcolorinput').value = this.colorSet[this.$$('#colorSelect').color];
        return this.colorSet[this.$$('#colorSelect').color];
    },
    _getEditColor: function () {
        if (this.$$('#colorSelect2').color == undefined) return "amber";
        this.$$('#colorField').value = this.colorSet[this.$$('#colorSelect2').color];
        return this.colorSet[this.$$('#colorSelect2').color];


    },
    _getColorSelected: function (color) {
        return Object.keys(this.colorSet).find(key => this.colorSet[key] === color);
    },
    _getTableDropDown: function (name) {
        if (name != undefined && name != "") {
            return this.fieldNames.indexOf(name);
        }
        return this.fieldNames.indexOf("none");
    },
    _getPredefinedExtractor: function (name) {
        if (name != undefined && name != "") return this.predefined_extractor_Array.indexOf(name);
        else return 0;

    },
    _getType: function (name) {
        if (name != undefined && name != "") return this.type.indexOf(name);
        else 0;
    },
    _getExtractorTarget: function (name) {
        if (name != undefined && name != "") return this.extractionTargetArray.indexOf(name);
        return 2;
    },
    _getSearchImportance: function (name) {
        if (name != undefined && name != "") return name - 1;
        return 0;
    },
    _getResult: function (name) {
        if (name != undefined && name != "") return this.show_in_resultArray.indexOf(name);
        else return 0;
    },
    _getLink: function (name) {
        if (name != undefined && name != "" && name != "none") return this.show_as_linkArray.indexOf(name);
        else return 0;
    },
    convertFileInputToFormData: function () {
        var file = this.$.input.inputElement.files[0];
        this.text = "";
        var reader = new FileReader();
        reader.onload = function () {
            this.text = reader.result;
        };
        reader.readAsText(file);
    },
    _itemSelected: function (e) {
        var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        var selectedValue = this.$$('#tableFieldInput').selectedItem.value;
        if (selectedValue == "none") selectedValue = "";
        this.$.updateTableAttribute.headers = obj;
        this.$.updateTableAttribute.url = backend_url + "projects/" + projectName + "/table_attributes/" + e.model.item[0].name;
        this.$.updateTableAttribute.body = JSON.stringify({
            "field_name": selectedValue,
            "info": e.model.item[0].info,
            "name": e.model.item[0].name,
            "value": e.model.item[0].value
        });
        this.$.updateTableAttribute.generateRequest();


    },
    onPresubmit: function (e) {
        var form = this.$.form;
        this.convertFileInputToFormData();
        form.request.body = this.text;
    },
    // saveFieldGlossaries: function () {
    //     this.fieldFormGlossaries = [];
    //     for (var i = 0; i < this.glossaries.length; i++) {
    //         var gloss = this.glossaries[i];
    //         if (this.$$('#' + gloss).checked) {
    //             this.fieldFormGlossaries.push(gloss[0]);
    //         }
    //     }
    //     glossariesNewField = this.fieldFormGlossaries;
    //     EditFieldGlossaries.toggle();
    // },

    setTableAttributes: function (data) {

        this.tableAttributes = [];
        if (Object.keys(data.detail.response).length != 0) {
            this.tableAttributes = Object.keys(data.detail.response).map(function (e) {
                return [data.detail.response[e]];
            });

            this.push('tableAttributes', this.tableAttributes.pop());

        }
    },

    fillTags: function (data) {
        if (data.detail.response.length != 0) {
            this.tags = Object.keys(data.detail.response).map(function (e) {
                return [data.detail.response[e]];
            });

            this.push('tags', this.tags.pop());

        }
    },
    fillFields: function (data) {
        if (data.detail.response.length != 0) {
            this.fields = Object.keys(data.detail.response).map(function (e) {
                return [data.detail.response[e]];
            });

            this.push('fields', this.fields.pop());
            this.fieldNames = [];
            for (var i = 0; i < this.fields.length; i++) {
                this.push('fieldNames', this.fields[i][0].name);
            }
            this.push('fieldNames', "none");
        }
        var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        this.$.tableAttributes.headers = obj;
        this.$.tableAttributes.url = backend_url + "projects/" + projectName + "/table_attributes";
        this.$.tableAttributes.generateRequest();
    },
    fillGlossary: function (data) {

        if (data.detail.response.length != 0) {
            data.detail.response.sort();
            this.glossaries = Object.keys(data.detail.response).map(function (e) {
                return [data.detail.response[e]];
            });
            this.push('glossaries', this.glossaries.pop());
        }

    },
    deleteTagsFunction: function (e) {
        var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        this.$.deleteTags.headers = obj;
        this.$.deleteTags.url = backend_url + "projects/" + projectName + "/tags/" + (e.model.item[0].name).split(":")[0];
        this.$.deleteTags.generateRequest();

    },
    editTagFunction: function (e) {
        this.tagForm = {};
        var tagName = e.model.item[0].name;
        var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        this.$.editTag.headers = obj;
        this.$.editTag.url = backend_url + "projects/" + projectName + "/tags/" + tagName;

        this.$.editTag.generateRequest();
        editTagsDialog.toggle();
    },
    updateTag: function (e) {
        var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        this.$.updateSavedTags.headers = obj;
        this.$.updateSavedTags.url = backend_url + "projects/" + projectName + "/tags/" + this.tagForm.name;
        this.$.updateSavedTags.body = JSON.stringify({
            "tag_name": this.tagForm.name + "",
            "tag_object": {
                "description": this.tagForm.description + "",
                "include_in_menu": this.tagForm.include_in_menu,
                "name": this.tagForm.name + "",
                "negative_class_precision": parseFloat(this.tagForm.negative_class_precision),
                "positive_class_precision": parseFloat(this.tagForm.positive_class_precision),
                "screen_label": this.tagForm.screen_label
            }
        });
        this.$.updateSavedTags.generateRequest();
        editTagsDialog.toggle();
    },
    updateDone: function () {
        var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        this.$.getFields.headers = obj;
        this.$.getFields.url = backend_url + "projects/" + projectName + "/fields";
        this.$.getFields.generateRequest();

        this.$.getTags.headers = obj;
        this.$.getTags.url = backend_url + "projects/" + projectName + "/tags";
        this.$.getTags.generateRequest();

        this.$.getGlossary.headers = obj;
        this.$.getGlossary.url = backend_url + "projects/" + projectName + "/glossaries";
        this.$.getGlossary.generateRequest();

        this.$.tableAttributes.headers = obj;
        this.$.tableAttributes.url = backend_url + "projects/" + projectName + "/table_attributes";
        this.$.tableAttributes.generateRequest();

    },
    sureToDeleteDialogFunction: function (e) {
        this.fieldName = e.model.item[0].name;
        sureToDeleteDialog.toggle();
    },
    sureToContinueExtractionFunction: function () {
        sureToContinueExtraction.toggle();
    },
    deleteFieldFunction: function () {
        sureToDeleteDialog.toggle();
        var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        this.$.deleteFields.headers = obj;
        this.$.deleteFields.url = backend_url + "projects/" + projectName + "/fields/" + this.fieldName;
        this.$.deleteFields.generateRequest();

    },
    deleteGlossaryFunction: function (e) {
        var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        this.$.deleteGlossaries.headers = obj;
        this.$.deleteGlossaries.url = backend_url + "projects/" + projectName + "/glossaries/" + (e.model.item[0]).split(":")[0];
        this.$.deleteGlossaries.generateRequest();
    },
    editFieldFunction: function (e) {
        var fieldFormName = e.model.item[0].name;

        var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        this.$.editField.headers = obj;
        this.$.editField.url = backend_url + "projects/" + projectName + "/fields/" + fieldFormName;

        this.$.editField.generateRequest();

        editFieldsDialog.toggle();

    },
    editGlossaryFunction: function (e) {
        this.glossaryForm = {};
        this.glossaryForm = e.model.item[0];
        editGlossariesDialog.toggle();
    },
    updateField: function (e) {
        var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        var predefinedExtr = "";

        //Save Glossaries
        this.fieldFormGlossaries = [];
        for (var i = 0; i < this.glossaries.length; i++) {
            var gloss = this.glossaries[i];
            if (this.$$('#' + gloss).checked) {
                this.fieldFormGlossaries.push(gloss[0]);
            }
        }

        if (this.$$('#editfieldpredefinedExtractor').selectedItem) {
            predefinedExtr = this.$$('#editfieldpredefinedExtractor').selectedItem.value;
        }
        this.$.updateSavedFields.headers = obj;
        this.$.updateSavedFields.url = backend_url + "projects/" + projectName + "/fields/" + this.fieldForm.name;
        if (this.fieldForm.screen_label == "") this.fieldForm.screen_label = this.fieldForm.name;
        if (this.fieldForm.screen_label_plural == "") this.fieldForm.screen_label_plural = this.fieldForm.screen_label;
        if (!this.fieldForm.group_name) this.fieldForm.group_name = "";
        this.$.updateSavedFields.body = JSON.stringify({
            "field_name": this.fieldForm.name,
            "field_object": {
                "color": this.fieldForm.color,
                "case_sensitive": this.fieldFormGlossaries.length > 0 ? this.fieldForm.case_sensitive : false,
                "combine_fields": this.fieldForm.combine_fields,
                "description": this.fieldForm.description,
                "glossaries": this.fieldFormGlossaries,
                "blacklists": this.fieldFormBlacklists,
                "group_name": this.fieldForm.group_name,
                "icon": this.fieldForm.icon,
                "name": this.fieldForm.name,
                "screen_label": this.fieldForm.screen_label,
                "screen_label_plural": this.fieldForm.screen_label_plural,
                "search_importance": parseInt(this.$$('#editSearchImpValue').selectedItem.value),
                "show_as_link": this.$$('#editlinkValue').selectedItem.value,
                "show_in_facets": this.fieldForm.show_in_facets,
                "show_in_result": this.$$('#editResultValue').selectedItem.value,
                "rule_extraction_target": this.$$('#editRuleExtractionTargetValue').selectedItem.value,
                "show_in_search": this.fieldForm.show_in_search,
                "rule_extractor_enabled": this.fieldForm.rule_extractor_enabled,
                "type": this.$$('#editTypeValue').selectedItem.value,
                "use_in_network_search": this.fieldForm.use_in_network_search,
                "predefined_extractor": predefinedExtr,
                "group_order": parseInt(this.fieldForm.group_order),
                "field_order": parseInt(this.fieldForm.field_order)
            }
        });
        this.$.updateSavedFields.generateRequest();
        editFieldsDialog.toggle();

    },
//	 inferlink:function() {
//		 var obj = {};
//		 obj.Authorization = "Basic " + btoa(username+":"+password);
//		 this.$.inferlink.headers = obj;
//		 var perPage = 0;
//		 var extraPage=0;
//
//		 perPage = this.$$('#perPage').value;
//		 extraPage = this.$$('#extraPage').value;
//		 var force=this.$$('#samplePageForce').checked;
//		 this.$.inferlink.url = backend_url +"projects/"+projectName+"/actions/get_sample_pages?pages_per_tld="+perPage+"&pages_extra="+extraPage+"&force_getting_sample_pages="+force;
//
//		 this.$.inferlink.generateRequest();
//	 },
//	 etk:function() {
//		 var obj = {};
//		 obj.Authorization = "Basic " + btoa(username+":"+password);
//		 this.$.etk.headers = obj;
//		 var force=this.$$('#etkForce').checked;
//		  this.$.etk.url = backend_url +"projects/"+projectName+"/actions/extract_and_load_test_data?force_start_new_extraction="+force;
//		  this.$.etk.body = JSON.stringify({
//			  "pages_per_tld_to_run": parseInt(this.$$("#etkTLD").value),
//			  "pages_extra_to_run": parseInt(this.$$("#etkExtraTLD").value),
//			  "lines_user_data_to_run":parseInt(this.$$("#etkLineField").value)
//		  });
//		 this.$.etk.generateRequest();
//	 },
//	 etkDeployed:function() {
//		 sureToContinueExtraction.toggle();
//		 var obj = {};
//		 obj.Authorization = "Basic " + btoa(username+":"+password);
//		 this.$.etkDeployed.headers = obj;
//		  this.$.etkDeployed.url = backend_url +"projects/"+projectName+"/actions/extract_and_load_deployed_data";
//
//		 this.$.etkDeployed.generateRequest();
//	 },
//
//	 publish:function() {
//		 var obj = {};
//		 obj.Authorization = "Basic " + btoa(username+":"+password);
//		 this.$.publish.headers = obj;
//
//		 this.$.publish.url = backend_url +"projects/"+projectName+"/actions/publish";
//
//		 this.$.publish.generateRequest();
//	 },
    done: function (data) {
        this.$$('#samplePageForce').checked = "";
        this.$$('#etkForce').checked = "";
        modalDialog.open();
    },
    successDone: function () {
        this.$$('#samplePageForce').checked = "";
        modalDialogSuccess.open();
    },
    successDoneIndex: function () {
        modalDialogSuccessIndex.open();
    },
    deletedGlossary: function () {
        this.glossaries = [];
        var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);

        this.$.getFields.headers = obj;
        this.$.getFields.url = backend_url + "projects/" + projectName + "/fields";
        this.$.getFields.generateRequest();

        this.$.getGlossary.headers = obj;
        this.$.getGlossary.url = backend_url + "projects/" + projectName + "/glossaries";
        this.$.getGlossary.generateRequest();
    },
//	 inferlinkGet:function() {
//
//
//		 var obj = {};
//		 obj.Authorization = "Basic " + btoa(username+":"+password);
//
//		 this.$.getAction1.headers = obj;
//		 this.$.getAction1.url = backend_url +"projects/"+projectName+"/actions/get_sample_pages";
//		 this.$.getAction1.generateRequest();
//
//	 },
//     getTLDInferlink: function (data) {
//         this.tldResponse = [];
//         this.tldResponse = Object.keys(data.detail.response).map(function (e) {
//             return [e, data.detail.response[e]];
//         });
//         if (this.tldResponse) showTLDsDialog.toggle();
//     },
//	 etkStatus:function() {
//		 var obj = {};
//		 this.$$("#etkForce").checked="";
//		 obj.Authorization = "Basic " + btoa(username+":"+password);
//
//
//		 this.$.etkGet.headers = obj;
//		 this.$.etkGet.url = backend_url +"projects/"+projectName+"/actions/extract_and_load_test_data";
//		 this.async(function() {
//			 this.$.etkGet.generateRequest();
//		   }, 2000);
//
//
//	 },
//	 etkdetails:function(data) {
//		 this.etkFields=[];
//		 this.etkFields = data.detail.response;
//
//		 if(this.etkFields.is_running ==false && this.etkFields.last_message=="done") {
//			 this.$.progr.querySelector("#primaryProgress").style.backgroundColor  = "green";
//		 }
//		 if(this.etkFields.is_running != false) {
//			 var obj = {};
//			 obj.Authorization = "Basic " + btoa(username+":"+password);
//
//
//			 this.$.etkGet.headers = obj;
//			 this.$.etkGet.url = backend_url +"projects/"+projectName+"/actions/extract_and_load_test_data";
//			 this.async(function() {
//				 this.$.etkGet.generateRequest();
//			   }, 2000);
//			 this.$.progr.querySelector("#primaryProgress").style.backgroundColor  = "#641ba7";
//
//		 }
//	 },
    _disableDocumentScrolling: function () {
        document.body.style.overflow = 'hidden';
    },
    _restoreDocumentScrolling: function () {
        document.body.style.overflow = '';
    },
    getFieldGlossary: function () {
        // console.log('getFieldGlossary');
        // console.log(this.glossaries);
        // console.log(this.fieldForm);
        // console.log(this.fieldForm.glossaries);
        // console.log(this.fieldFormGlossaries);

        EditFieldGlossaries.toggle();
        for (var j = 0; j < this.glossaries.length; j++) {
            this.$$('#' + this.glossaries[j][0]).checked = "";

        }

        if (this.fieldForm) {
            if (this.fieldForm.glossaries) {
                for (var i = 0; i < this.fieldForm.glossaries.length; i++) {
                    for (var j = 0; j < this.glossaries.length; j++) {
                        if (this.fieldForm.glossaries[i] == this.glossaries[j][0]) {
                            this.$$('#' + this.glossaries[j][0]).checked = "true";
                            break;
                        }
                    }
                }
            }
        }

        if (this.fieldFormGlossaries) {
            for (var i = 0; i < this.fieldFormGlossaries.length; i++) {
                for (var j = 0; j < this.glossaries.length; j++) {
                    if (this.fieldFormGlossaries[i] == this.glossaries[j][0]) {
                        this.$$('#' + this.glossaries[j][0]).checked = "true";
                        break;
                    }
                }
            }
        }
    },

    getFieldGlossariesForAdd: function () {
        EditFieldGlossaries.toggle();

        if (glossariesNewField) {
            for (var i = 0; i < glossariesNewField.length; i++) {
                for (var j = 0; j < this.glossaries.length; j++) {
                    if (glossariesNewField[i] == this.glossaries[j][0]) {
                        this.$$('#' + this.glossaries[j][0]).checked = "true";
                        break;
                    }
                }

            }

        } else {
            glossariesNewField = [];
            for (var i = 0; i < this.glossaries.length; i++) {
                var gloss = this.glossaries[i];
                if (this.$$('#' + gloss).checked) {
                    glossariesNewField.push(gloss[0]);
                }
            }
        }
    },

    getFieldBlacklist: function () {
        // console.log('getFieldBlacklist');
        // console.log(this.glossaries);
        // console.log(this.fieldForm);
        // console.log(this.fieldForm.blacklists);
        // console.log(this.fieldFormBlacklists);

        EditFieldBlacklists.toggle();

        // clean up checked state
        for (var j = 0; j < this.glossaries.length; j++) {
            this.$$('#bl-' + this.glossaries[j][0]).checked = "";
        }

        // check remote items
        if (this.fieldForm) {
            if (this.fieldForm.blacklists) {
                for (var i = 0; i < this.fieldForm.blacklists.length; i++) {
                    for (var j = 0; j < this.glossaries.length; j++) {
                        if (this.fieldForm.blacklists[i] == this.glossaries[j][0]) {
                            this.$$('#bl-' + this.glossaries[j][0]).checked = "true";
                            break;
                        }
                    }
                }
            }
        }

        // check temp items
        if (this.fieldFormBlacklists) {
            for (var i = 0; i < this.fieldFormBlacklists.length; i++) {
                for (var j = 0; j < this.glossaries.length; j++) {
                    if (this.fieldFormBlacklists[i] == this.glossaries[j][0]) {
                        this.$$('#bl-' + this.glossaries[j][0]).checked = "true";
                        break;
                    }
                }
            }
        }
    },

    getFieldBlacklistsForAdd: function () {
        EditFieldBlacklists.toggle();

        if (blacklistsNewField) {
            for (var i = 0; i < blacklistsNewField.length; i++) {
                for (var j = 0; j < this.glossaries.length; j++) {
                    if (blacklistsNewField[i] == this.glossaries[j][0]) {
                        this.$$('#bl-' + this.glossaries[j][0]).checked = "true";
                        break;
                    }
                }

            }

        } else {
            blacklistsNewField = [];
            for (var i = 0; i < this.glossaries.length; i++) {
                var gloss = this.glossaries[i];
                if (this.$$('#bl-' + gloss).checked) {
                    blacklistsNewField.push(gloss[0]);
                }
            }
        }
    },

//	updateToNewIndex:function() {
//		 var obj = {};
//		 obj.Authorization = "Basic " + btoa(username+":"+password);
//
//		 this.$.updateIndex.headers = obj;
//		 this.$.updateIndex.url = backend_url +"projects/"+projectName+"/actions/update_to_new_index";
//		 this.$.updateIndex.generateRequest();
//	},
//	updateToNewIndexNew:function() {
//		 var obj = {};
//		 obj.Authorization = "Basic " + btoa(username+":"+password);
//
//		 this.$.updateIndexNew.headers = obj;
//		 this.$.updateIndexNew.url = backend_url +"projects/"+projectName+"/actions/update_to_new_index_deployed";
//		 this.$.updateIndexNew.generateRequest();
//	},

    getIconNames: function (iconset) {
        return iconset.getIconNames();
    },
    downloadGlossaryFunction: function (e) {

        var request = new XMLHttpRequest();
        var url = backend_url + "projects/" + projectName + "/glossaries/" + e.model.item[0];

        request.open("GET", url);
        request.setRequestHeader("Content-type", "application/gzip");
        request.setRequestHeader("Content-Transfer-Encoding", "binary");
        // request.setRequestHeader("Authorization", "Basic " + btoa(username + ":" + password));
        request.responseType = "blob";
        request.onreadystatechange = function () {
            if (request.readyState === 4 && request.status === 200) {
                var element = document.createElement('a');
                blob = new Blob([request.response], {type: "application/gzip"}),
                    url = window.URL.createObjectURL(blob);
                element.setAttribute('href', url);

                element.setAttribute('download', request.getResponseHeader("Content-Disposition").split("=")[1]);

                element.style.display = 'none';
                document.body.appendChild(element);
                element.click();

                document.body.removeChild(element);
                window.URL.revokeObjectURL(url);
            }
        };

        request.send();

    },
    editRules: function (e) {
        // var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        // this.$.editSpacyRules.headers = obj;

        this.$.editSpacyRules.url = backend_url + "projects/" + projectName + "/fields/" + this.fieldForm.name + "/spacy_rules?type=all";
        this.$.editSpacyRules.generateRequest();
        spacyRulesDialog.toggle();

    },
    editRulesNextDialog: function (e) {
        var url = spacy_ui_url + "#/" + spacy_backend_auth_base64 + "/" + spacy_backend_sever_name_base64 + "/" + projectName + "/" + this.fieldForm.name;
        window.open(url, '_blank');
    },
    editRulesAdd: function () {
        var url = spacy_ui_url + "#/" + spacy_backend_auth_base64 + "/" + spacy_backend_sever_name_base64 + "/" + projectName + "/" + this.$$('#fieldnameinput').value;
        window.open(url, '_blank');
    },
    editRulesNext: function (e) {
        var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        // this.$.editSpacyRulesNext.headers = obj;

        this.$.editSpacyRulesNext.url = spacy_ui_url + "#/" + spacy_backend_auth_base64 + "/" + spacy_backend_sever_name_base64 + "/" + projectName + "/" + this.fieldForm.name;
        this.$.editSpacyRulesNext.body = (this.$$('#spacyRulesNextTextArea').value);

        this.$.editSpacyRulesNext.generateRequest();
        spacyRulesNextDialog.toggle();
    },
    fieldSpacyRules: function (data) {
        this.spacyRules = [];
        this.$$('#spacyRulesTextArea').value = JSON.stringify(data.detail.response);
    },
    updateFieldSpacyRules: function () {
        // var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        // this.$.updateSpacyRules.headers = obj;

        this.$.updateSpacyRules.url = backend_url + "projects/" + projectName + "/fields/" + this.fieldForm.name + "/spacy_rules";

        this.$.updateSpacyRules.body = (this.$$('#spacyRulesTextArea').value);
        this.$.updateSpacyRules.generateRequest();
        spacyRulesDialog.toggle();
    },
    showSpacyRuleDummy: function () {
        this.$$('#spacyRulesTextArea').value = '{"rules": [],"test_text": "string"}';
    },
    setIcon: function (e) {
        this.$$('#fieldiconinput').value = e.model.item;
        papericonSet.toggle();
    },
    setEditIcon: function (e) {
        this.$$('#iconField').value = e.model.item;
        papericonEditSet.toggle();
    },
    setEditFieldForm: function (data) {
        this.fieldFormGlossaries = [];
        this.fieldFormBlacklists = [];
        this.fieldForm = [];
        this.fieldForm = data.detail.response;
        for (var j = 0; j < this.glossaries.length; j++) {
            this.$$('#' + this.glossaries[j][0]).checked = "";
            this.$$('#bl-' + this.glossaries[j][0]).checked = "";
        }
        if (this.fieldForm) {
            if (this.fieldForm.glossaries) {
                for (var i = 0; i < this.fieldForm.glossaries.length; i++) {
                    for (var j = 0; j < this.glossaries.length; j++) {
                        if (this.fieldForm.glossaries[i] == this.glossaries[j][0]) {
                            this.$$('#' + this.glossaries[j][0]).checked = "true";
                            break;
                        }
                    }
                }
            }

            if (this.fieldForm.blacklists) {
                for (var i = 0; i < this.fieldForm.blacklists.length; i++) {
                    for (var j = 0; j < this.glossaries.length; j++) {
                        if (this.fieldForm.blacklists[i] == this.glossaries[j][0]) {
                            this.$$('#bl-' + this.glossaries[j][0]).checked = "true";
                            break;
                        }
                    }
                }
            }
        }
    },
    addNewFieldSetup: function () {
        addFieldDialog.toggle();
        glossariesNewField = [];
        blacklistsNewField = [];
        this.$$("#fieldnameinput").value = "";
        this.$$("#fielddescriptioninput").value = "";
        this.$$("#fieldscreenlabelinput").value = "";
        this.$$("#fieldscreenlabelPluralinput").value = "";
        this.$$("#fieldcolorinput").value = "amber";
        this.$$("#getCaseSenstive").checked = "";


        this.$$("#fieldgroupnameinput").value = "";
        this.$$("#fieldiconinput").value = "icons:default";
        this.$$("#fieldsearchinput").selected = "0";
        this.$$("#fieldtypeinput").selected = "0";
        this.$$("#fieldRuleExtractor").checked = false;
        this.$$("#fieldpredefinedExtractor").selected = "0";

        this.$$("#fieldcombinedfieldsinput").checked = false;
        this.$$("#fieldfacetinput").checked = false;
        this.$$("#fieldlinkinput").selected = "0";
        this.$$("#fieldresultinput").selected = "0";
        this.$$("#fieldsearchinput2").checked = false;
        this.$$("#fieldnetworkinput").checked = false;
        this.$$("#fieldRuleExtractorTarget").selected = "2";
    },
    saveTempGlossaries: function () {
        this.fieldFormGlossaries = [];
        glossariesNewField = [];
        for (var i = 0; i < this.glossaries.length; i++) {
            var gloss = this.glossaries[i];
            if (this.$$('#' + gloss).checked) {
                this.fieldFormGlossaries.push(gloss[0]);
            }
        }
        glossariesNewField = this.fieldFormGlossaries;
    },
    saveTempBlacklists: function () {
        this.fieldFormBlacklists = [];
        blacklistsNewField = [];
        for (var i = 0; i < this.glossaries.length; i++) {
            var gloss = this.glossaries[i];
            if (this.$$('#bl-' + gloss).checked) {
                this.fieldFormBlacklists.push(gloss[0]);
            }
        }
        blacklistsNewField = this.fieldFormBlacklists;
    },
    addNewAttribute: function () {
        this.$$("#tableAttributeInputValue").value = "";
        this.$$("#fieldInputDropDownInput").selected = "";
        this.$$("#textAreaForTableAttribute").value = "";

        AddNewTableAttributeDialog.toggle();
    },
    deleteAttribute: function (e) {
        // var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        // this.$.deleteTableAttribute.headers = obj;

        this.$.deleteTableAttribute.url = backend_url + "projects/" + projectName + "/table_attributes/" + e.model.item[0].name;
        this.$.deleteTableAttribute.generateRequest();

    },
    getToHome: function () {
        location.href = ".";
    },
    checkLength: function (item) {
        return item[0].glossaries && item[0].glossaries.length && item[0].glossaries.length > 0;

    },
    submitImportProjectConfigForm: function() {
        if(window.confirm("Are you sure to upload and overwrite current project config?") == false) {
            return;
        }

        var importFileFormData = new FormData();
        var file = $("#importProjectConfigDialog paper-input[type=file] input")[0].files[0];
        importFileFormData.append("file_data", file);

        $.ajax({
            type: "POST",
            url: backend_url + "projects/" + projectName + '/actions/project_config',
            dataType: "json",
            context: this,
            data: importFileFormData,
            async: true,
            processData: false,
            contentType: false,
            success: function (data) {
                alert("project config imported");
                // update ui
                this.updateDone();
            },
            error: function() {
                alert("fail to import project config");
            }
        });
    },
    exportProject: function() {
        // $.ajax({
        //     type: "GET",
        //     url: backend_url + "projects/" + projectName + '/actions/master_config',
        //     dataType: "json",
        //     context: this,
        //     async: true,
        //     processData: false,
        //     success: function (data) {
        //         $("<a />", {
        //             "download": "master_config.json",
        //             "href" : "data:application/json," + encodeURIComponent(JSON.stringify(data, null, 2))
        //         }).appendTo("body").click(function() {
        //             $(this).remove();
        //         })[0].click()
        //     }
        // });


        var url = backend_url + "projects/" + projectName + '/actions/project_config';
        var request = new XMLHttpRequest();
        request.open("GET", url);
        request.setRequestHeader("Content-type", "application/gzip");
        request.setRequestHeader("Content-Transfer-Encoding", "binary");
        request.responseType = "blob";
        request.onreadystatechange = function () {
            if (request.readyState === 4 && request.status === 200) {
                var element = document.createElement('a');
                blob = new Blob([request.response], {type: "application/gzip"}),
                    url = window.URL.createObjectURL(blob);
                element.setAttribute('href', url);
                element.setAttribute('download', request.getResponseHeader("Content-Disposition").split("=")[1]);
                element.style.display = 'none';
                document.body.appendChild(element);
                element.click();
                document.body.removeChild(element);
                window.URL.revokeObjectURL(url);
            } else if(request.readyState === 4 && request.status != 200) {
                alert("fail to export project config");
            }
        }
        request.send();
    },
//	uploadSamplePages:function() {
//		uploadZipFileDialog.toggle();
//	}
    refreshTldTable: function(useTimeout=false) {
        if(useTimeout) {
            setTimeout($.proxy(this.refreshTldTable, this, {useTimeout: true}), REFRESH_TLD_TABLE_INTERVAL);
        }
        console.log("refresh tld table");
        $.ajax({
            type: "GET",
            url: backend_url + "projects/" + projectName + '/actions/extract?value=tld_statistics',
            dataType: "json",
            context: this,
            async: true,
            processData: false,
            // headers: {
            //     "Authorization": AUTH_HEADER
            // },
            success: function (data) {
                // console.log(data);
                var total_tld = 0;
                var total_total_num = 0;
                var total_es_num = 0;
                var total_es_original_num = 0;
                var total_desired_num = 0;
                newTldTableData = [];
                data["tld_statistics"].forEach(function(obj) {
                    var disable_landmark_btn = obj["total_num"] < 10 ? " disabled" : "";
                    var disable_delete_btn = obj["total_num"] < 1 ? " disabled" : "";
                    newObj = {
                        "tld": obj["tld"].toLowerCase(),
                        "total_num": obj["total_num"],
                        "es_num": obj["es_num"],
                        "es_original_num": obj["es_original_num"],
                        "desired_num": obj["desired_num"],
                        "landmark": "<paper-icon-button icon=\"icons:add-box\" raised class=\"btnAddToLandmark\" data-tld=\""+obj["tld"]+"\"" + disable_landmark_btn + ">Add</paper-icon-button>",
                        "delete": "<paper-icon-button icon=\"icons:delete-forever\" raised class=\"btnDeleteFileData\" data-tld=\""+obj["tld"]+"\"" + disable_delete_btn + ">Delete</paper-icon-button>"
                    };
                    total_tld += 1;
                    total_total_num += obj["total_num"];
                    total_es_num += obj["es_num"];
                    total_es_original_num += obj["es_original_num"];
                    total_desired_num += obj["desired_num"];
                    newTldTableData.push(newObj);
                });

                this.tldTableData = newTldTableData;
                this.$.tldTable.reload();

                // because default paper-datatable doesn't support dynamic header
                // this is a hacking, need to change if there's a good way
                // console.log(this.$.tldTableTLD.header);
                // this.$.tldTableTLD.header = 'TLD (' + total_tld.toString() + ')';
                $("#tldTable div#container table thead tr th span").each(function(index) {
                    if(index == 0) {
                        $(this).text("TLD (" + total_tld.toString() + ")");
                    }
                    else if(index == 1) {
                        $(this).text("Total (" + total_total_num.toString() + ")");
                    }
                    else if(index == 2) {
                        $(this).text("KG (" + total_es_num.toString() + ")");
                    }
                    else if(index == 3) {
                        $(this).text("KG Original (" + total_es_original_num.toString() + ")");
                    }
                    else if(index == 4) {
                        $(this).text("Desired (" + total_desired_num.toString() + ")");
                    }
                });
            }
        });
    },
    sortCaseInsensitive: function(a, b) {
        return a.toLowerCase().localeCompare(b.toLowerCase());
    },
    refreshPipelineStatus: function(useTimeout=false) {
        if(useTimeout) {
            setTimeout($.proxy(this.refreshPipelineStatus, this, {useTimeout: true}), REFRESH_PIPELINE_STATUS_INTERVAL);
        }
        console.log("refresh pipeline status");
        $.ajax({
            type: "GET",
            url: backend_url + "projects/" + projectName + '/actions/extract?value=etk_status',
            dataType: "json",
            context: this,
            async: true,
            processData: false,
            // headers: {
            //     "Authorization": AUTH_HEADER
            // },
            success: function (data) {
                // console.log(data);
                if(data["etk_status"]) {
                    this.updatePipelineBtn(true);
                } else {
                    this.updatePipelineBtn(false);
                }
            }
        });
    },
    submitImportFileForm: function() {
        var importFileFormData = new FormData();
        var file = $("#importFileFormDialog paper-input[type=file] input")[0].files[0];
        importFileFormData.append("file_data", file);
        importFileFormData.append("file_name", file.name);
        importFileFormData.append("file_type", "json_lines");

        this.updateProgressBar(0);
        this.$.progressDialog.toggle();

        $.ajax({
            type: "POST",
            url: backend_url + "projects/" + projectName + '/data',
            dataType: "json",
            context: this,
            data: importFileFormData,
            async: true,
            processData: false,
            contentType: false,
            // headers: {
            //     "Authorization": AUTH_HEADER
            // },
            xhr: function() {
                // console.log(this.context);
                var xhr = new window.XMLHttpRequest();
                xhr.upload.context = this.context;
                xhr.upload.addEventListener("progress", function(evt) {
                    // console.log(evt.target.context);
                    if (evt.lengthComputable) {
                        var percentComplete = evt.loaded / evt.total;
                        percentComplete = parseInt(percentComplete * 100);
                        // console.log(percentComplete);
                        evt.target.context.updateProgressBar(percentComplete);

                        if (percentComplete === 100) {
                        }
                    }
                }, false);

                return xhr;
            },
            success: function (data) {
                this.refreshTldTable();
            },
            complete: function() {
                this.$.progressDialog.toggle();
            }
        });
    },
    updateProgressBar: function(percentage) {
        $("#progressDialog paper-progress").first().attr("value", percentage)
    },
    addToLandmark: function(e) {
        var tld = $(e.currentTarget).attr("data-tld");
        payload = {
            "tlds": {
               [tld] : 100
            }
        };
        // console.log(payload);
        $.ajax({
            type: "POST",
            url: backend_url + "projects/" + projectName + '/actions/landmark_extract',
            async: true,
            dataType: "json",
            processData: false,
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(payload),
            // headers: {
            //     "Authorization": AUTH_HEADER
            // },
            success: function (msg) {
                // console.log(msg);
                alert("Added")
            }
        });
        // console.log(tld);
    },
    deleteFileData: function(e) {

        if(window.confirm("Are you sure to data of this TLD?") == false) {
            return;
        }

        var tld = $(e.currentTarget).attr("data-tld");
        payload = {"tlds":[tld]};

        $.ajax({
            type: "DELETE",
            url: backend_url + "projects/" + projectName + '/data',
            async: true,
            dataType: "json",
            processData: false,
            context: this,
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(payload),
            success: function (msg) {
            }
        });
    },
    openDIGUI: function() {
        var url = digui_url + "?project=" + projectName;
        window.open(url, '_blank');
    },
    openLandmarkTool: function() {
        var url = landmark_url + "#/project/select?prefix=" + projectName;
        window.open(url, '_blank');
    },
    openKibana: function() {
        var url = kibana_url;
        window.open(url, '_blank');
    },
    switchPipeline: function() {
        console.log("current pipeline status: " + this.etkStatus);
        // force to update button status
        // //(overwrite default behavior of paper-toggle-button)
        this.updatePipelineBtn(this.etkStatus);

        if(this.etkStatus) { // current on, need to turn off

            if(window.confirm("Turn off pipeline?") == false) {
                console.log("turn off");
                return;
            }
            $.ajax({
                type: "DELETE",
                url: backend_url + "projects/" + projectName + '/actions/extract',
                async: true,
                dataType: "json",
                processData: false,
                context: this,
                success: function (msg) {
                    this.updatePipelineBtn(false);
                },
                error: function(msg) {
                    alert("Can not turn off pipeline");
                    console.log(msg);
                }
            });
        } else {

            if(window.confirm("Turn on pipeline?") == false) {
                return;
            }
            $.ajax({
                type: "POST",
                url: backend_url + "projects/" + projectName + '/actions/extract',
                async: true,
                dataType: "json",
                processData: false,
                context: this,
                success: function (msg) {
                    this.updatePipelineBtn(true);
                },
                error: function(msg) {
                    alert("Can not turn on pipeline (Make sure you've created config and mapping)");
                    console.log(msg);
                }
            });
        }
    },
    updatePipelineBtn: function(pipeline_on) {
        if(pipeline_on) {
            this.etkStatus = true;
            // this.$.btnSwitchPipeline.textContent = "Turn off Pipeline";
            this.$.btnSwitchPipeline.checked = true;
        } else {
            this.etkStatus = false;
            // this.$.btnSwitchPipeline.textContent = "Turn on Pipeline";
            this.$.btnSwitchPipeline.checked = false;
        }
    },
    recreateMapping: function() {
        if(window.confirm("Are you sure to recreate ElasticSearch Mapping and restart pipeline?") == false) {
            return;
        }
        // loadingDialog.toggle();
        // console.log("recreate");
        $.ajax({
            type: "POST",
            url: backend_url + "projects/" + projectName + '/actions/recreate_mapping',
            async: true,
            dataType: "json",
            contentType: false,
            processData: false,
            context: this,
            // headers: {
            //     "Authorization": AUTH_HEADER
            // },
            success: function (msg) {
                // console.log(msg);
                alert("Mapping recreated and data is adding in the backend.");
                this.updatePipelineBtn(true);
            },
            error: function(msg) {
                alert('Can not recreate mapping');
                console.log(msg);
            }
        });
    },
    reloadBlacklist: function() {
        if(window.confirm("Are you sure to update KG (blacklists) and restart pipeline?") == false) {
            return;
        }

        $.ajax({
            type: "POST",
            url: backend_url + "projects/" + projectName + '/actions/reload_blacklist',
            async: true,
            dataType: "json",
            contentType: false,
            processData: false,
            context: this,
            success: function (msg) {
                // console.log(msg);
                alert("KG data reloaded to queue.");
                this.updatePipelineBtn(true);
            },
            error: function(msg) {
                alert('Can not update KG (blacklists)');
                console.log(msg);
            }
        });
    },
    updateDesiredNumber: function() {
        var num = parseInt(this.$.globalDesiredNumber.value);
        num = num <= 9999999999 ? num : 999999999;
        num = num >= 0 ? num : 0;

        payload = {"tlds":{}};
        this.tldTableData.forEach(function(obj){
            payload["tlds"][[obj["tld"]]] = num;
        });

        $.ajax({
            type: "POST",
            url: backend_url + "projects/" + projectName + '/actions/desired_num',
            async: true,
            dataType: "json",
            processData: false,
            context: this,
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(payload),
            // headers: {
            //     "Authorization": AUTH_HEADER
            // },
            success: function (msg) {
                // console.log(msg);
                this.refreshTldTable();
            }
        });
    },
    addDataToQueue: function() {

        $.ajax({
            type: "POST",
            url: backend_url + "projects/" + projectName + '/actions/add_data',
            async: true,
            dataType: "json",
            processData: false,
            context: this,
            contentType: 'application/json; charset=utf-8',
            // headers: {
            //     "Authorization": AUTH_HEADER
            // },
            success: function (msg) {
                alert("Adding data to queue in the backend");
            }
        });
    },
    fetchCatalogError: function() {
        $.ajax({
            type: "GET",
            url: backend_url + "projects/" + projectName + '/data?type=error_log',
            dataType: "json",
            context: this,
            async: true,
            processData: false,
            // headers: {
            //     "Authorization": AUTH_HEADER
            // },
            success: function (msg) {
                // console.log(msg["error_log"]);
                $("#logDialog .logDialogContent:first").empty();
                msg["error_log"].forEach(function(ele) {
                    $("<p>"+ele+"</p>").appendTo("#logDialog .logDialogContent:first");
                });
                this.$.logDialog.toggle();
            }
        });
    },
    deleteAllFileData: function() {

        if(window.confirm("Are you sure to delete all data?") == false) {
            return;
        }

        payload = {"tlds":[]};
        this.tldTableData.forEach(function(obj){
            payload["tlds"].push(obj["tld"]);
        });

        $.ajax({
            type: "DELETE",
            url: backend_url + "projects/" + projectName + '/data',
            async: true,
            dataType: "json",
            processData: false,
            context: this,
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(payload),
            success: function (msg) {
                // console.log(msg);
                // this.refreshTldTable();
            }
        });
    },
    updateFilters: function() {
        try {
            var payload = {"filters": JSON.parse(this.$$('#editFiltersTextArea').value)};
        } catch(e) {
            alert("Invalid JSON");
            return;
        }
        // console.log(JSON.stringify(payload));
        $.ajax({
            type: "POST",
            url: backend_url + "projects/" + projectName + '/actions/etk_filters',
            dataType: "json",
            contentType: 'application/json; charset=utf-8',
            context: this,
            async: true,
            processData: false,
            data: JSON.stringify(payload),
            success: function (msg) {
                this.$.editFiltersDialog.toggle();
            },
            error: function (data) {
                // console.log(data);
                if(data.status === 400) {
                    alert('Invalid filters: ' + data.responseJSON.error_message);
                }
            }
        });
    },
    editFilters: function() {
        // fill in latest filters
        $.ajax({
            type: "GET",
            url: backend_url + "projects/" + projectName + '/actions/etk_filters',
            dataType: "json",
            context: this,
            async: true,
            processData: false,
            contentType: 'application/json; charset=utf-8',
            success: function (msg) {
                this.$$('#editFiltersTextArea').value = JSON.stringify(msg["filters"], undefined, 4);
                this.$.editFiltersDialog.toggle();
            }
        });
    },
    sortFields: function(obj1, obj2) {
        var a = obj1[0]["name"].toLowerCase();
		var b = obj2[0]["name"].toLowerCase();
		if (a < b) return -1;
		else if (a > b) return 1;
		else return 0;
    },
    sortTags: function(obj1, obj2) {
        var a = obj1[0]["name"].toLowerCase();
		var b = obj2[0]["name"].toLowerCase();
		if (a < b) return -1;
		else if (a > b) return 1;
		else return 0;
    },
    sortGlossaries: function(obj1, obj2) {
        var a = obj1[0].toLowerCase();
		var b = obj2[0].toLowerCase();
		if (a < b) return -1;
		else if (a > b) return 1;
		else return 0;
    },


    /*
        navigation
    */
    navAction: function() {
        this.$.navTabAction.style.backgroundColor = NAV_BG_COLOR;
        this.$.navTabField.style.backgroundColor = null;
        this.$.navTabTag.style.backgroundColor = null;
        this.$.navTabGlossary.style.backgroundColor = null;
        this.$.navTabTable.style.backgroundColor = null;

        this.$.tabTag.opened = false;
        this.$.tabAction.opened = true;
        this.$.tabGlossary.opened = false;
        this.$.tabField.opened = false;
        this.$.tabTable.opened = false;
    },
    navGlossary: function () {
        this.$.navTabAction.style.backgroundColor = null;
        this.$.navTabField.style.backgroundColor = null;
        this.$.navTabTag.style.backgroundColor = null;
        this.$.navTabGlossary.style.backgroundColor = NAV_BG_COLOR;
        this.$.navTabTable.style.backgroundColor = null;

        this.$.tabField.opened = false;
        this.$.tabTag.opened = false;
        this.$.tabGlossary.opened = true;
        this.$.tabAction.opened = false;
        this.$.tabTable.opened = false;
    },
    navField: function() {
        this.$.navTabAction.style.backgroundColor = null;
        this.$.navTabField.style.backgroundColor = NAV_BG_COLOR;
        this.$.navTabTag.style.backgroundColor = null;
        this.$.navTabGlossary.style.backgroundColor = null;
        this.$.navTabTable.style.backgroundColor = null;

        this.$.tabTag.opened = false;
        this.$.tabGlossary.opened = false;
        this.$.tabField.opened = true;
        this.$.tabAction.opened = false;
        this.$.tabTable.opened = false;
    },
    navTable: function() {
        this.$.navTabAction.style.backgroundColor = null;
        this.$.navTabField.style.backgroundColor = null;
        this.$.navTabTag.style.backgroundColor = null;
        this.$.navTabGlossary.style.backgroundColor = null;
        this.$.navTabTable.style.backgroundColor = NAV_BG_COLOR;

        this.$.tabTag.opened = false;
        this.$.tabGlossary.opened = false;
        this.$.tabField.opened = false;
        this.$.tabAction.opened = false;
        this.$.tabTable.opened = true;
    },
    navTag: function() {
        this.$.navTabAction.style.backgroundColor = null;
        this.$.navTabField.style.backgroundColor = null;
        this.$.navTabTag.style.backgroundColor = NAV_BG_COLOR;
        this.$.navTabGlossary.style.backgroundColor = null;
        this.$.navTabTable.style.backgroundColor = null;

        this.$.tabField.opened = false;
        this.$.tabGlossary.opened = false;
        this.$.tabTag.opened = true;
        this.$.tabAction.opened = false;
        this.$.tabTable.opened = false;
    }
});