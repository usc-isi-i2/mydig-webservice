var dataText;
var glossariesNewField = [];
var blacklistsNewField = [];
var projectName = window.location.href.split('?')[1];
var NAV_BG_COLOR = "rgba(255, 255, 0, 0.22)";
var REFRESH_TLD_TABLE_INTERVAL = 10000; // 10s
var REFRESH_PIPELINE_STATUS_INTERVAL = 10000; // 10s


poly = Polymer({
    is: 'project-details',

    ready: function () {
        this.fields = [];
        this.tags = [];
        this.glossaryFormField = [];
        this.glossaries = [];
        this.fieldFormGlossaries = [];
        this.tagsData = [];
        this.fieldsData = [];
        this.tableAttributes = [];
        this.fieldNames = [];
        this.etkStatus = false;
        this.scope =[]
        this.scope.parentNode={}
        this.iconsetRepeat ={}
        this.newField = {}
        this.fieldForm = {}
        this.newFieldColor = "#ffb300"
        this.editFieldColor = "#263238"
        this.disablelandMark = false;
        this.disableDelete =false;
        this.total_tld = 0;
        this.total_num = 0;
        this.total_es_num = 0;
        this.total_desired_num = 0;
        this.total_es_original_num=0;
        this.loadFlag =0;
        this.dialogText =""
        this.confirmText =""
        this.confirmButton =""
        this.fucntionButton  = ""
        this.confirmValue =0
        this.pipelineCall=0
        this.disableColor = "#666666"

        this.scope.getIconNames = function(iconset) {
        return iconset.getIconNames();
        //console.log("heree");
      };

      this.iconsetRepeat = new Polymer.IronMeta({type: 'iconset'}).list;
      //console.log(this.iconsetRepeat[0]._icons);

      /*for(var i=0;i<iconsetRepeat.size();i++)
      {
        if(i==0)
            {
                scope[i]=[]
            }
        scope[i].push
      }
*/
        this.scope.parentNode.getIconNames = this.scope.getIconNames;

       /* this.iconsets = this.iconset;*/
       /* //console.log(iconset.getOwnPropertyNames());
        //console.log(Polymer.getOwnPropertyNames())*/

        this.$.projectNameHeader.textContent = "Project: " + projectName;

        this.updateDone(); // update all tabs
        this.navAction();
        this.refreshPipelineStatus(true);
        this.refreshTldTable(true);

        this.tldTableData = [];
        // this.$.tldTable.sort = this.sortCaseInsensitive;
       

        $(document).on('tap', '.btnAddToLandmark', this.addToLandmark);

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
        //this.$.actions.focus();
    },
    submitGlossaryFormData: function(){
        var glossName = this.$$("#glossary_nameInput").value;
    if (/\s/.test(glossName)) {
        return;
    }
    var file = this.$$("#glossary_fileInput").inputElement.inputElement.files[0];
    var url = backend_url + "projects/" + projectName + "/glossaries";
//------------
    var formData = new FormData();

    formData.append("glossary_name", glossName);
    formData.append("glossary_file", file); // number 123456 is immediately converted to a string "123456"
    // //console.log(formData);

    var request = new XMLHttpRequest()
    request.open("POST", url);
//  request.setRequestHeader("Content-type", "application/json");
    request.onreadystatechange = function () {
        if (request.readyState === 4 && request.status === 201) {
 
            this.$$("#glossary_nameInput").value = "";
           this.$$("#addGlossaryDialog").toggle();
           this.$$("#getGlossary").generateRequest();
        }
    }.bind(this);

    request.send(formData);

    },
    getIconNames: function(iconset) {
        return iconset.getIconNames();
      },
    setNewIconColor: function()
    {
        /*//console.log(this.$$('#newColorSelect').node);
*/        if (this.$$('#newColorSelect').color == undefined) return "amber";
        this.newFieldColor= this.$$('#newColorSelect').color;
        return this.$$('#newColorSelect').color
    },
    goToLandMark: function(e)
    {
        ////console.log("there" + e.target.value);
       window.open("http://www."+e.target.value, '_blank');
    },
    _getColor: function () {
        if (this.$$('#colorSelect').color == undefined) return "#ffb300";
        this.$$('#fieldcolorinput').value = this.colorSet[this.$$('#colorSelect').color];
        return this.colorSet[this.$$('#colorSelect').color];
    },
    _getEditColor: function () {
        if (this.$$('#colorSelect2').color == undefined) {
            this.editFieldColor = "#ffb300";
            this.$$('#papericonEditSet').style.fill = this.editFieldColor;
            return "amber";
        }
        this.editFieldColor = this.$$('#colorSelect2').color;
        //console.log(this.editFieldColor);

        this.$$('#papericonEditSet').style.fill = this.editFieldColor;
       /* getComputedStyle(this.$$('#iconField'))*/
      this.$$('#iconField').style.color = this.editFieldColor ;
        return this.colorSet[this.$$('#colorSelect2').color];


    },
    _getColorSelected: function (color) {
        /*return 0*/
        
        if (color!= undefined)
        {
            //console.log("color is "+this.colorSet[color]);
            if(this.colorSet[color] == undefined){

                //console.log("here");
                this.editFieldColor = Object.keys(this.colorSet).find(key => this.colorSet[key] === color);
            return Object.keys(this.colorSet).find(key => this.colorSet[key] === color)}
             else{
                this.editFieldColor = color;
                return color;
            }
        }
            this.editFieldColor = "#ffb300";
            this.$$('#papericonEditSet').style.fill = this.editFieldColor;
            return "#ffb300";
        
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
    saveFieldGlossaries: function () {
        this.fieldFormGlossaries = [];
        for (var i = 0; i < this.glossaries.length; i++) {
            var gloss = this.glossaries[i];
            if (this.$$('#' + gloss).checked) {
                this.fieldFormGlossaries.push(gloss[0]);
            }
        }
        glossariesNewField = this.fieldFormGlossaries;
        EditFieldGlossaries.toggle();
    },

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
        this.$.tableAttributes.headers = obj;
        this.$.tableAttributes.url = backend_url + "projects/" + projectName + "/table_attributes";
        this.$.tableAttributes.generateRequest();
        //console.log(this.fields);
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
        this.$.deleteTags.headers = obj;
        this.$.deleteTags.url = backend_url + "projects/" + projectName + "/tags/" + (e.model.item[0].name).split(":")[0];
        this.$.deleteTags.generateRequest();

    },
    editTagFunction: function (e) {
        this.tagForm = {};
        var tagName = e.model.item[0].name;
        var obj = {};
        this.$.editTag.headers = obj;
        this.$.editTag.url = backend_url + "projects/" + projectName + "/tags/" + tagName;

        this.$.editTag.generateRequest();
        editTagsDialog.toggle();
    },
    updateTag: function (e) {
        var obj = {};
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
    updateDesiredDialogFunction:function(){
        this.$$('#updateDesiredDialog').toggle();
       
    },
    updateDone: function () {
        var obj = {};
        // console.log("im here");
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
        this.$$('#sureToDeleteDialog').toggle();
        /*var dialog = document.querySelector('#sureToDeleteDialog');
        this.setDialog(true);
        dialog.open();*/
        },
        callImportFileFormDialog: function (e) {
        this.$$('#importFileFormDialog').toggle();
        /*var dialog = document.querySelector('#sureToDeleteDialog');
        this.setDialog(true);
        dialog.open();*/
        },
        importProjectFunction: function () {
        this.$$('#importProjectConfigDialog').toggle();
        /*var dialog = document.querySelector('#sureToDeleteDialog');
        this.setDialog(true);
        dialog.open();*/
        },
        deleteAllFileData: function(e) {

        if($(e.currentTarget)[0].id != "yes")
        {
            this.confirmText = "Are you sure to delete all data?"
            this.confirmButton = "Delete"
            this.listen(this.$$("#yes"), 'tap', 'deleteAllFileData');
            this.$$('#confirmDialog').toggle();
            return
        }
       
        

        payload = {"tlds":[], "from": "file"};
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
                this.unlisten(this.$$("#yes"), 'tap', 'deleteAllFileData');
                // //console.log(msg);
                // this.refreshTldTable();
            }
        });
    },
  /*  setDialog: function (open) {
            if (open) {
                var node = document.querySelector('#sureToDeleteDialog');
                var textnode = document.querySelector("body");
                textnode.appendChild(node);
            } else {
                var node = document.querySelector('#sureToDeleteDialog');
                var textnode = document.querySelector("top-nav");
                textnode.appendChild(node);
            }
        },*/
    sureToContinueExtractionFunction: function () {
        sureToContinueExtraction.toggle();
    },
    deleteFieldFunction: function () {
        this.$$('#sureToDeleteDialog').toggle();
        var obj = {};
        this.$.deleteFields.headers = obj;
        this.$.deleteFields.url = backend_url + "projects/" + projectName + "/fields/" + this.fieldName;
        this.$.deleteFields.generateRequest();

    },
    deleteGlossaryFunction: function (e) {
        if($(e.currentTarget)[0].id != "yes")
        {
            this.confirmText = "Are you sure to delete this glossary ?"
            this.confirmButton = "Delete"
            this.confirmValue = e.model.item[0];
            this.listen(this.$$("#yes"), 'tap', 'deleteGlossaryFunction');
            this.$$('#confirmDialog').toggle();
            return
        }

        var obj = {};
        this.$.deleteGlossaries.headers = obj;
        this.$.deleteGlossaries.url = backend_url + "projects/" + projectName + "/glossaries/" + (e.currentTarget.value).split(":")[0];
        this.$.deleteGlossaries.generateRequest();
        this.unlisten(this.$$("#yes"), 'tap', 'deleteGlossaryFunction');
    },
    editFieldFunction: function (e) {
        var fieldFormName = e.model.item[0].name;
         this.$.editFieldsDialog.toggle();

        console.log(fieldFormName);

        var obj = {};
        this.$.editField.headers = obj;
        this.$.editField.url = backend_url + "projects/" + projectName + "/fields/" + fieldFormName;

        this.$.editField.generateRequest();

       /* //console.log(fieldForm.icon);*/

       

    },
    editGlossaryFunction: function (e) {
        this.glossaryForm = {};
        this.glossaryForm = e.model.item[0];
        this.$$("#editGlossariesDialog").toggle();
    },
    openFile: function(e)
    {
        var input = event.target;
        var reader = new FileReader();
        reader.onload = function () {
            dataText = reader.result;

        };
        reader.readAsText(this.$$('#glossary_file').inputElement.inputElement.files[0]);
    },
    updateGlossaryFormData: function()
    {
        var glossName = this.$$('#glossary_name').value;
        var file = this.$$('#glossary_file').inputElement.inputElement.files[0]
        /*//console.log($('#glossInput')[0].files[0]);*/


    var url = backend_url + "projects/" + projectName + "/glossaries/" + glossName;
    //------------
    var formData = new FormData();

    formData.append("glossary_name", glossName);
    formData.append("glossary_file", file); // number 123456 is immediately converted to a string "123456"
    // //console.log(formData);

    var request = new XMLHttpRequest();
    request.open("POST", url);
    //  request.setRequestHeader("Content-type", "application/json");

    request.onreadystatechange = function () {
        if (request.readyState === 4 && request.status === 201) {
            this.$$("#editGlossariesDialog").toggle();
            this.$$("#getGlossary").generateRequest();
        }
    }.bind(this);

    request.send(formData);
    },
    updateField: function (e) {
        var obj = {};
        var predefinedExtr = "";

        //Save Glossaries
        this.fieldFormGlossaries = [];
        for (var i = 0; i < this.glossaries.length; i++) {
            var gloss = this.glossaries[i];
            if (this.$$('#' + gloss).checked) {
                this.fieldFormGlossaries.push(gloss[0]);
            }
        }


        //console
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
                "color": this.colorSet[this.editFieldColor],
                "case_sensitive": this.fieldFormGlossaries.length > 0 ? this.fieldForm.case_sensitive : false,
                "combine_fields": this.fieldForm.combine_fields,
                "description": this.fieldForm.description,
                "glossaries": this.fieldFormGlossaries,
                "blacklists": this.fieldFormBlacklists,
                "group_name": this.fieldForm.group_name,
                "icon": this.$$('#iconField').icon,
                "name": this.fieldForm.name,
                "screen_label": this.fieldForm.screen_label,
                "screen_label_plural": this.fieldForm.screen_label_plural,
                "search_importance": parseInt(this.$$('#editSearchImpValue').selectedItem.value),
                "show_as_link": this.$$('#editlinkValue').selectedItem.value,
                "show_in_facets": this.fieldForm.show_in_facets,
                "show_in_result": this.$$('#editResultValue').selectedItem.value,
                /*"rule_extraction_target": this.$$('#editRuleExtractionTargetValue').selectedItem.value,*/
                "show_in_search": this.fieldForm.show_in_search,
                "rule_extractor_enabled": this.fieldForm.rule_extractor_enabled,
                "type": this.$$('#editTypeValue').selectedItem.value,
                "use_in_network_search": this.fieldForm.use_in_network_search,
                "predefined_extractor": predefinedExtr,
                "group_order": parseInt(this.fieldForm.group_order),
                "field_order": parseInt(this.fieldForm.field_order),
                "free_text_search": this.fieldForm.free_text_search
            }
        });
        this.$.updateSavedFields.generateRequest();
        this.$$('#editFieldsDialog').toggle();

    },
    done: function (data) {
        /*this.$$('#samplePageForce').checked = "";
        this.$$('#etkForce').checked = "";*/
        this.$$('#modalDialog').open();
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

        this.$.getFields.headers = obj;
        this.$.getFields.url = backend_url + "projects/" + projectName + "/fields";
        this.$.getFields.generateRequest();

        this.$.getGlossary.headers = obj;
        this.$.getGlossary.url = backend_url + "projects/" + projectName + "/glossaries";
        this.$.getGlossary.generateRequest();
    },
    _disableDocumentScrolling: function () {
        document.body.style.overflow = 'hidden';
    },
    _restoreDocumentScrolling: function () {
        document.body.style.overflow = '';
    },
    getFieldGlossary: function () {
        this.$$('#EditFieldGlossaries').toggle();
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
        this.$$('#EditFieldGlossaries').toggle();

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
        // //console.log('getFieldBlacklist');
        // //console.log(this.glossaries);
        // //console.log(this.fieldForm);
        // //console.log(this.fieldForm.blacklists);
        // //console.log(this.fieldFormBlacklists);

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

    getIconNames: function (iconset) {
        return iconset.getIconNames();
    },
    downloadGlossaryFunction: function (e) {

        var request = new XMLHttpRequest();
        var url = backend_url + "projects/" + projectName + "/glossaries/" + e.model.item[0];

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
            }
        };

        request.send();

    },
    editRules: function (e) {
        // var obj = {};
        // this.$.editSpacyRules.headers = obj;

        this.$.editSpacyRules.url = backend_url + "projects/" + projectName + "/fields/" + this.fieldForm.name + "/spacy_rules?type=all";
        this.$.editSpacyRules.generateRequest();
        this.$$('#spacyRulesDialog').toggle();

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
       /* //console.log($(e.currentTarget));
        //console.log($(e.currentTarget)[0]);
        //console.log($(e.currentTarget)[0].__data.icon);*/
        this.$$('#fieldInputIcon').icon = $(e.currentTarget)[0].__data.icon;
        this.$$('#papericonSet').toggle();
    },
    toggleEditIcons: function(){
        this.$$('#editDialogIcons').style.fill = this.$$("#colorSelect2").color;
        this.$$('#papericonEditSet').toggle();
    },
    setEditIcon: function (e) {
        this.$$('#iconField').icon = $(e.currentTarget)[0].__data.icon;
        this.$$('#iconField').style.color = this.$$("#colorSelect2").color;
        this.$$('#papericonEditSet').toggle();
    },
    setEditFieldForm: function (data) {
        this.fieldFormGlossaries = [];
        this.fieldForm = [];
        this.fieldForm = data.detail.response;
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
        this.$$('#addFieldDialog').toggle();
        glossariesNewField = [];
        blacklistsNewField = [];
        this.$$("#fieldnameinput").value = "";
        this.$$("#fielddescriptioninput").value = "";
        this.$$("#fieldscreenlabelinput").value = "";
        this.$$("#fieldscreenlabelPluralinput").value = "";
       /* this.$$("#fieldcolorinput").value = "amber";*/
        this.$$("#getCaseSenstive").checked = "";


        this.$$("#fieldgroupnameinput").value = "";
/*        this.$$("#fieldiconinput").value = "";*/
        this.$$('#fieldInputIcon').icon = "star";
        this.$$("#fieldsearchinput").selected = 0;
        this.$$("#fieldtypeinput").selected = 0;
        this.$$("#fieldRuleExtractor").checked = false;
        this.$$("#fieldpredefinedExtractor").selected = 0;

        this.$$("#fieldcombinedfieldsinput").checked = false;
        this.$$("#fieldfacetinput").checked = false;
        this.$$("#fieldlinkinput").selected = 0;
        this.$$("#fieldresultinput").selected = 0;
        this.$$("#fieldsearchinput2").checked = false;
        this.$$("#fieldnetworkinput").checked = false;
        this.$$('#groupOrderInput').value="";
        this.$$('#fieldOrderInput').value="";
        this.$$("#free_text_search").checked = false;
        /*this.$$("#fieldRuleExtractorTarget").selected = "2";*/
    },
    getFieldBlacklist: function () {
        // //console.log('getFieldBlacklist');
        // //console.log(this.glossaries);
        // //console.log(this.fieldForm);
        // //console.log(this.fieldForm.blacklists);
        // //console.log(this.fieldFormBlacklists);

        

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
        this.$$('#EditFieldBlacklists').toggle();
    },
    getFieldBlacklistsForAdd: function () {
        this.$$('#EditFieldBlacklists').toggle();

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
    addNewField: function(){

    var xhr = new XMLHttpRequest();
    var url = backend_url + "projects/" + projectName + "/fields";
    var name = this.$$("#fieldnameinput").value;
    if (/\s/.test(name)) {
        return;
    }
    var description = this.$$("#fielddescriptioninput").value;
    var screenlabel = this.$$("#fieldscreenlabelinput").value;
    var screen_label_plural = this.$$("#fieldscreenlabelPluralinput").value;
    if (screenlabel == "") screenlabel = name;
    if (screen_label_plural == "") screen_label_plural = screenlabel;

    if (this.colorSet[this.newFieldColor] ==undefined)
        var color = "#ffb300";
    else
        var color = this.colorSet[this.newFieldColor];
    var type = this.$$("#fieldtypeinput").selectedItem.value;
    var predefinedExtractor = "";
    if (this.$$("#fieldpredefinedExtractor").selectedItem) {
        predefinedExtractor = this.$$("#fieldpredefinedExtractor").selectedItem.value;
    }

    var groupname = this.$$("#fieldgroupnameinput").value;
    var icon = this.$$("#fieldInputIcon").icon;
    var searchimp = parseInt(this.$$("#fieldsearchinput").selectedItem.value);
    var ruleExtractor = this.$$("#fieldRuleExtractor").checked;
    var combinefields = this.$$("#fieldcombinedfieldsinput").checked;
    var facet = this.$$("#fieldfacetinput").checked;
    var link = this.$$("#fieldlinkinput").selectedItem.value;
    var result = this.$$("#fieldresultinput").selectedItem.value;
    var search = this.$$("#fieldsearchinput2").checked;
    var networksearch = this.$$("#fieldnetworkinput").checked;
    var groupOrder = parseInt(this.$$("#groupOrderInput").value);
    var fieldOrder = parseInt(this.$$("#fieldOrderInput").value);
     var free_text_search = this.$$("#field_free_text_search").checked;

   /* var ruleextractTarget = this.$$("#fieldRuleExtractorTarget").selectedItem.value;*/
    var caseSense = this.$$("#getCaseSenstive").checked;
    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-type", "application/json");

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 201) {
            this.$$("#addFieldDialog").toggle();
            this.$$("#getFields").generateRequest();
            glossariesNewField = [];
            this.$$("#fieldnameinput").value = "";
            this.$$("#fielddescriptioninput").value = "";
            this.$$("#fieldscreenlabelinput").value = "";
            this.$$("#fieldscreenlabelPluralinput").value = "";
           /* this.$$("#fieldcolorinput").value = "amber";*/
           this.newFieldColor = "#ffb300";
           this.$$('#newColorSelect').color = this.newFieldColor;

            this.$$("#getCaseSenstive").checked = "";


            this.$$("#fieldgroupnameinput").value = "";
            this.$$("#fieldInputIcon").icon = "star";
            this.$$("#fieldsearchinput").selected = 0;
            this.$$("#fieldtypeinput").selected = 0;
            this.$$("#fieldRuleExtractor").checked = false;
            this.$$("#fieldpredefinedExtractor").selected = 0;

            this.$$("#fieldcombinedfieldsinput").checked = false;
            this.$$("#fieldfacetinput").checked = false;
            this.$$("#fieldlinkinput").selected = 0;
            this.$$("#fieldresultinput").selected = 0;
            this.$$("#fieldsearchinput2").checked = false;
            this.$$("#fieldnetworkinput").checked = false;
            this.$$("#groupOrderInput").value = "";
            this.$$("#fieldOrderInput").value = "";
            this.$$("#free_text_search").checked = false;
            
            /*document.getElementById("fieldRuleExtractorTarget").selected = "2";*/

        }
    }.bind(this);

    var data = JSON.stringify({
        "field_name": name,
        "field_object": {
            "color": color,
            "case_sensitive": caseSense,
            "combine_fields": combinefields,
            "description": description,
            "glossaries": glossariesNewField,
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
            "group_order": groupOrder,
            "field_order": fieldOrder,
            "free_text_search": free_text_search
            /*"rule_extraction_target": ruleextractTarget*/
        }
    });

    xhr.send(data);

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
    submitImportProjectConfigForm: function(e) {


         if($(e.currentTarget)[0].id != "yes")
        {
            this.confirmText = "Are you sure to upload and overwrite current project config?"
            this.confirmButton = "Overwrite"
            this.listen(this.$$("#yes"), 'tap', 'submitImportProjectConfigForm');
            this.$$('#confirmDialog').toggle();
            return
        }
        /*if(window.confirm("Are you sure to upload and overwrite current project config?") == false) {
            return;
        }*/

        var importFileFormData = new FormData();
        var file = this.$$('#projectInput').inputElement.inputElement.files[0]
       /* //console.log($("#importProjectConfigDialog paper-input[type=file] input")[0].files[0]);*/
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
                this.dialogText = "Project config imported";
                this.$$('#alertDialog').toggle();
                // update ui
                this.updateDone();
                this.unlisten(this.$$("#yes"), 'tap', 'submitImportProjectConfigForm');
            },
            error: function() {
                this.dialogText = "Failed to import project config";
                this.$$('#alertDialog').toggle();
                this.unlisten(this.$$("#yes"), 'tap', 'submitImportProjectConfigForm');
                /*alert();*/
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


        var url = backend_url + "projects/" + projectName + '/actions/project_config?_t=' + Date.now().toString();
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
                this.dialogText = "Failed to export project config";
                this.$$('#alertDialog').toggle();
                
            }
        }
        request.send();
    },
//	uploadSamplePages:function() {
//		uploadZipFileDialog.toggle();
//	}
    deleteFileData: function(e) {


        if($(e.currentTarget)[0].id != "yes")
        {
            this.confirmText = "Are you sure to delete the data of this TLD?"
            this.confirmButton = "DELETE"
            this.confirmValue = $(e.currentTarget)[0].value
            this.listen(this.$$("#yes"), 'tap', 'deleteFileData');
            this.$$('#confirmDialog').toggle();
            return
        }
        /*if(window.confirm("Are you sure to data of this TLD?") == false) {
            return;
        }*/

        var tld = $(e.currentTarget)[0].value;
        //console.log($(e.currentTarget)[0].value);
        payload = {"tlds":[tld], "from": "file"};

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
                //console.log("success");
                this.unlisten(this.$$("#yes"), 'tap', 'deleteFileData');
            },
            error :function(xhr, ajaxOptions, thrownError)
            {
                this.unlisten(this.$$("#yes"), 'tap', 'deleteFileData');
                //console.log("error");
                //console.log(xhr);
            }
        });
    },
    refreshTldTable: function(useTimeout=false) {
        if(useTimeout) {
            setTimeout($.proxy(this.refreshTldTable, this, {useTimeout: true}), REFRESH_TLD_TABLE_INTERVAL);
        }
        //console.log("refresh tld table");
        $.ajax({
            type: "GET",
            url: backend_url + "projects/" + projectName + '/actions/extract?value=tld_statistics',
            dataType: "json",
            context: this,
            async: true,
            processData: false,
            success: function (data) {
                // //console.log(data);
                var total_tld = 0;
                var total_total_num = 0;
                var total_es_num = 0;
                var total_desired_num = 0;
                var total_es_original_num=0;
                newTldTableData = [];
                data["tld_statistics"].forEach(function(obj) {
                    var disable_landmark_btn = obj["total_num"] < 10 ? true : false;
                    var disable_delete_btn = obj["total_num"] < 1 ? true : false;
                    cbt = "#263238";
                    cl = "#263238";

                    if (disable_delete_btn) {
                       cbt = "#B0B0B0";
                    }
                    if (disable_landmark_btn) {
                        cl = "#B0B0B0";
                    }
                    //console.log(disable_delete_btn);
                    //console.log(disable_landmark_btn);
                    newObj = {
                        "tld": obj["tld"].toLowerCase(),
                        "total_num": obj["total_num"],
                        "es_num": obj["es_num"],
                        "desired_num": obj["desired_num"],
                        "disable_Landmark": disable_landmark_btn,
                        "color_l": cl,
                        "color_btn": cbt,
                        "disable_Delete" : disable_delete_btn
                    };
                    total_tld += 1;
                    total_total_num += obj["total_num"];
                    total_es_num += obj["es_num"];
                    total_desired_num += obj["desired_num"];
                    total_es_original_num += obj["es_original_num"];
                    newTldTableData.push(newObj);

                }
                );


                this.total_tld = total_tld;
                this.total_num =total_total_num;
                this.total_desired_num =total_desired_num;
                this.total_es_num = total_es_num;
                this.total_es_original_num = total_es_original_num;
                this.tldTableData = newTldTableData;

                //console.log(this.tldTableData);

                if(this.loadFlag==0)
                    {
                        this.loadFlag =1;
                        this.$$('#tldHeader').click();
                    }

                //Polymer.dom(this.$$('#tldHeader')).click();
                /*//console.log(Polymer.dom(*//*));*/
                //this.$.tldTable.reload();

                // because default paper-datatable doesn't support dynamic headera
                // this is a hacking, need to change if there's a good way
                // //console.log(this.$.tldTableTLD.header);
                // this.$.tldTableTLD.header = 'TLD (' + total_tld.toString() + ')';
               /* $("#tldTable div#container table thead tr th span").each(function(index) {
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
                        $(this).text("Desired (" + total_desired_num.toString() + ")");
                    }
                });*/
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
    sortCaseInsensitive: function(a, b) {
        return a.toLowerCase().localeCompare(b.toLowerCase());
    },
    refreshPipelineStatus: function(useTimeout=false) {
        if(useTimeout) {
            setTimeout($.proxy(this.refreshPipelineStatus, this, {useTimeout: true}), REFRESH_PIPELINE_STATUS_INTERVAL);
        }
        //console.log("refresh pipeline status");
        $.ajax({
            type: "GET",
            url: backend_url + "projects/" + projectName + '/actions/extract?value=etk_status',
            dataType: "json",
            context: this,
            async: true,
            processData: false,
            success: function (data) {
                // //console.log(data);
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
        var file = this.$$("#fileInput").inputElement.inputElement.files[0]
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
            xhr: function() {
                // //console.log(this.context);
                var xhr = new window.XMLHttpRequest();
                xhr.upload.context = this.context;
                xhr.upload.addEventListener("progress", function(evt) {
                    // //console.log(evt.target.context);
                    if (evt.lengthComputable) {
                        var percentComplete = evt.loaded / evt.total;
                        percentComplete = parseInt(percentComplete * 100);
                        // //console.log(percentComplete);
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
        // //console.log(payload);
        $.ajax({
            type: "POST",
            url: backend_url + "projects/" + projectName + '/actions/landmark_extract',
            async: true,
            dataType: "json",
            processData: false,
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(payload),
            success: function (msg) {
                // //console.log(msg);
                this.dialogText = "Added";
                this.$$('#alertDialog').toggle();
            }.bind(this)
        });
        // //console.log(tld);
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
    switchPipeline: function(e) {
        //console.log("current pipeline status: " + this.etkStatus);
        // force to update button status
        // //(overwrite default behavior of paper-toggle-button)
         if($(e.currentTarget)[0].value!=1)
            this.updatePipelineBtn(this.etkStatus);

        //console.log(this.etkStatus);
        //console.log(this.confirmValue);
        
       

        if(this.etkStatus) { // current on, need to turn off
       
        if($(e.currentTarget)[0].id != "yes")
        {
            this.confirmText = "Turn off pipeline ?"
            this.confirmButton = "YES"
            this.confirmValue =1
            /*this.confirmValue = $(e.currentTarget)[0].value*/

            this.listen(this.$$("#yes"), 'tap', 'switchPipeline');
            this.$$('#confirmDialog').toggle();
            return
            
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
                    this.pipelineCall =0
                },
                error: function(msg) {
                    this.dialogText = "Can not turn off pipeline";
                this.$$('#alertDialog').toggle();
                this.pipelineCall =0
                    //console.log(msg);
                }
            });

            this.confirmValue =0
        } 
        else {
          
           if($(e.currentTarget)[0].id != "yes")
            {
            this.confirmText = "Turn on pipeline ?"
            this.confirmButton = "YES"
            this.confirmValue =1
            console.log("here")
            /*this.confirmValue = $(e.currentTarget)[0].value*/
            this.listen(this.$$("#yes"), 'tap', 'switchPipeline');
            /*this.functionButton = "switchPipeline"*/
            this.$$('#confirmDialog').toggle();
            return
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
                    this.pipelineCall =0
                },
                error: function(msg) {
                   /* alert("Can not turn on pipeline (Make sure you've created config and mapping)");*/
                    this.dialogText = "Can not turn on pipeline (Make sure you've created config and mapping)";
                this.$$('#alertDialog').toggle();
                this.pipelineCall =0
                    //console.log(msg);
                }
            });
            this.confirmValue =0
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
    recreateMapping: function(e) {

        if($(e.currentTarget)[0].id != "yes")
        {
            this.confirmText = "Are you sure to recreate ElasticSearch Mapping and restart pipeline?"
            this.confirmButton = "YES"
            /*this.confirmValue = $(e.currentTarget)[0].value*/
            this.listen(this.$$("#yes"), 'tap', 'recreateMapping');
            this.$$('#confirmDialog').toggle();
            return
        }
        /*if(window.confirm("Are you sure to recreate ElasticSearch Mapping and restart pipeline?") == false) {
            return;
        }*/
        // loadingDialog.toggle();
        // //console.log("recreate");
        $.ajax({
            type: "POST",
            url: backend_url + "projects/" + projectName + '/actions/recreate_mapping',
            async: true,
            dataType: "json",
            contentType: false,
            processData: false,
            context: this,
            success: function (msg) {
                // //console.log(msg);
                this.dialogText = "Mapping recreated and data is adding in the backend.";
                this.$$('#alertDialog').toggle();
                this.updatePipelineBtn(true);
                this.unlisten(this.$$("#yes"), 'tap', 'recreateMapping');
            },
            error: function(msg) {
                this.dialogText = "Cannot recreate Mapping";
                this.$$('#alertDialog').toggle();
                this.unlisten(this.$$("#yes"), 'tap', 'recreateMapping');
                //console.log(msg);
            }
        });
    },
    updateSingleDesired: function(e)
    {
        num = parseInt(e.srcElement.value);
        //console.log(e.srcElement.id);
        id = e.srcElement.id;
        /*num = num <= 9999999999 ? num : 999999999;
        num = num >= 0 ? num : 0;*/
        payload = {"tlds":{}};
        payload["tlds"][[id]]= num;
        ////console.log(payload)

         $.ajax({
            type: "POST",
            url: backend_url + "projects/" + projectName + '/actions/desired_num',
            async: true,
            dataType: "json",
            processData: false,
            context: this,
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(payload),
            success: function (msg) {
                 ////console.log("updated");
                this.refreshTldTable();
            }
        });
    },
    updateDesiredNumber: function() {
        var num = parseInt(this.$.globalDesiredNumber.value);
        this.$$('#updateDesiredDialog').toggle();
        num = num <= 9999999999 ? num : 999999999;
        num = num >= 0 ? num : 0;
        //console.log("im here")

        payload = {"tlds":{}};
        this.tldTableData.forEach(function(obj){
            payload["tlds"][[obj["tld"]]] = num;
            ////console.log(obj["tld"]);
        });

        ////console.log(payload)

        $.ajax({
            type: "POST",
            url: backend_url + "projects/" + projectName + '/actions/desired_num',
            async: true,
            dataType: "json",
            processData: false,
            context: this,
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify(payload),
            success: function (msg) {
                // //console.log(msg);
                this.refreshTldTable();
            }
        });
    },
    toggleIcons()
    {
        this.$$("#papericonSet").toggle();
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
            success: function (msg) {
                this.dialogText = "Adding data to queue in the backend";
                this.$$('#alertDialog').toggle();
            }
        });
    },
    toggleGlossary: function()
    {
        this.$$('#addGlossaryDialog').toggle();
    },
    fetchCatalogError: function() {
        $.ajax({
            type: "GET",
            url: backend_url + "projects/" + projectName + '/data?type=error_log',
            dataType: "json",
            context: this,
            async: true,
            processData: false,
            success: function (msg) {
                // //console.log(msg["error_log"]);
              Polymer.dom(this.$$("#logDialogContent")).innerHTML ="";
              var s="";
                msg["error_log"].forEach(function(ele) {
                   s=s+"<p>"+ele+"</p>";
                    /*this.$$("#logDialogContent").html("blahaahah")*/
                });
                 Polymer.dom(this.$$("#logDialogContent")).innerHTML =s;
                this.$.logDialog.toggle();
            }
        });
    },
    updateFilters: function() {
        try {
            var payload = {"filters": JSON.parse(this.$$('#editFiltersTextArea').value)};
        } catch(e) {
            this.dialogText = "Invalid JSON";
                this.$$('#alertDialog').toggle();
            return;
        }
        // //console.log(JSON.stringify(payload));
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
                // //console.log(data);
                if(data.status === 400) {
                    this.dialogText = 'Invalid filters: ' + data.responseJSON.error_message;
                    this.$$('#alertDialog').toggle();
                    
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


    /*
        navigation
    */
    navAction: function() {
        this.$.navTabAction.style.backgroundColor = NAV_BG_COLOR;
        this.$.navTabField.style.backgroundColor = null;
      /*  this.$.navTabTag.style.backgroundColor = null;*/
        this.$.navTabGlossary.style.backgroundColor = null;
      /*  this.$.navTabTable.style.backgroundColor = null;*/

      /*  this.$.tabTag.opened = false;*/
        this.$.tabAction.opened = true;
        this.$.tabGlossary.opened = false;
        this.$.tabField.opened = false;
       /* */
    },
    navGlossary: function () {
        this.$.navTabAction.style.backgroundColor = null;
        this.$.navTabField.style.backgroundColor = null;
       /* this.$.navTabTag.style.backgroundColor = null;*/
        this.$.navTabGlossary.style.backgroundColor = NAV_BG_COLOR;
      /*  this.$.navTabTable.style.backgroundColor = null;*/

        this.$.tabField.opened = false;
/*        this.$.tabTag.opened = false;*/
        this.$.tabGlossary.opened = true;
        this.$.tabAction.opened = false;
/*        this.$.tabTable.opened = false;*/
    },
    navField: function() {
        this.$.navTabAction.style.backgroundColor = null;
        this.$.navTabField.style.backgroundColor = NAV_BG_COLOR;
        // this.$.navTabTag.style.backgroundColor = null;
        this.$.navTabGlossary.style.backgroundColor = null;
    /*    this.$.navTabTable.style.backgroundColor = null;*/

   /*     this.$.tabTag.opened = false;*/
        this.$.tabGlossary.opened = false;
        this.$.tabField.opened = true;
        this.$.tabAction.opened = false;
       /* this.$.tabTable.opened = false;*/
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
    },
    projectSettingsFunction : function() {
        var url = "/mydig/projects/" +projectName;

        var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        this.$.getProjectSettings.headers = obj;
        this.$.getProjectSettings.url = "/mydig/projects/" +projectName;

        this.$.getProjectSettings.generateRequest();

        this.$$('#projectSettingsDialog').toggle();
    },
    ProjectSettingsDialogSetup: function(data) {

        this.projectSettingsObject = [];
        this.projectSettingsObject = data.detail.response;
        //console.log(this.projectSettingsObject);


        if(this.projectSettingsObject.show_images_in_facets)
            this.$$('#imageFacets').checked=true;
        else this.$$('#imageFacets').checked=false;
        if(this.projectSettingsObject.show_images_in_search_form)
            this.$$('#searchFormImages').checked=true;
        else this.$$('#searchFormImages').checked=false;
        if(this.projectSettingsObject.hide_timelines)
            this.$$('#hideTimelines').checked=true;
        else this.$$('#hideTimelines').checked=false;



        /*for (var j = 0; j < this.glossaries.length; j++) {
            this.$$('#' + this.glossaries[j][0]).checked = "";

        }*/
        /*if (this.fieldForm) {
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
        }*/


    },
    saveProjectSettings: function() {
        var obj = {};
        // obj.Authorization = "Basic " + btoa(username + ":" + password);
        var predefinedExtr = "";



        //console

        this.$.updateProjectSettings.headers = obj;
        this.$.updateProjectSettings.url = backend_url + "/projects/" + projectName;
        /*console.log(this.projectSettingsObject.show_images_in_facets)*/
        this.projectSettingsObject.new_linetype = this.$$("#newlineType").value
        //console.log(this.projectSettingsObject.new_linetype);
        this.projectSettingsObject.image_prefix = this.$$("#imagePrefix").value;
        this.projectSettingsObject.default_desired_num =  parseInt(this.$$('#defaultDesiredNum').value);
        this.projectSettingsObject.show_images_in_facets = this.$$('#imageFacets').checked;
        this.projectSettingsObject.show_images_in_search_form =this.$$('#searchFormImages').checked;
        this.projectSettingsObject.hide_timelines =this.$$('#hideTimelines').checked;

        /*if(projectSettingsObject.imagePrefix == undefined)
        {
            projectSettingsObject.imagePrefix = ""
        }*/
        this.$.updateProjectSettings.body = JSON.stringify({
            "image_prefix": this.projectSettingsObject.image_prefix == undefined ? "" : this.projectSettingsObject.image_prefix ,
            "default_desired_num": this.projectSettingsObject.default_desired_num == undefined ? 0 : this.projectSettingsObject.default_desired_num,
            "show_images_in_facets": this.projectSettingsObject.show_images_in_facets == undefined ? false : this.projectSettingsObject.show_images_in_facets,
            "show_images_in_search_form": this.projectSettingsObject.show_images_in_search_form == undefined ? false : this.projectSettingsObject.show_images_in_search_form,
            "hide_timelines": this.projectSettingsObject.hide_timelines ==undefined ? false : this.projectSettingsObject.hide_timelines,
            "new_linetype": this.projectSettingsObject.new_linetype ==undefined ? "break" : this.projectSettingsObject.new_linetype.toLowerCase()
        });
        this.$.updateProjectSettings.generateRequest();
        this.$$('#projectSettingsDialog').toggle();


    },
    get_newlineType: function(value)
    {
        arr = ["break", "newline"]
        //console.log(value);
       if (value != undefined && value != "") return arr.indexOf(value);
        else return 0;
    }
});
