/* 
 * Copyright 2014 Medical Research Council Harwell.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/* global d3 */

/**
 * 
 * Written by: Gagarine Yaikhom (g.yaikhom@har.mrc.ac.uk)
 */
(function () {

    /* this is the global variable where we expose the public interfaces */
    if (typeof dcc === 'undefined')
        dcc = {};

    dcc.imageviewerVersion = 'DCC_IMAGEVIEWER_VERSION';
    dcc.mediaContextForQC = null;

    var isDragging = false, dragX, dragY, syncControls = false,
        body = window.document.body,
        oldBodySelectStartHandler = body.onselectstart,
        oldBodyMouseUpHandler = body.onmouseup,
        /* The following keeps track of the mouse events that are attached with
         * the body of the documents */
        mouseDown = false,
        floatingPointRegEx = /^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$/,
        dateFormatter = d3.time.format('%e %B %Y, %A'),
        PREFERRED_IMAGE_FORMAT = '.jpg',
        TILE_SIZE = 256,
        THUMBNAIL_WIDTH = 240,
        /* Change this if you are including script from another web app */
        IMAGE_VIEWER_HOST = '',
        /* Root directory of the tiles on image server */
        IMAGE_SERVER = 'https://www.mousephenotype.org/images/',
        IMAGE_TILE_SERVER = IMAGE_SERVER + 'tiles/',
        ORIGINAL_MEDIA_SERVER = IMAGE_SERVER + 'src/',
        EMBRYO_MEDIA_SERVER = IMAGE_SERVER + 'emb/',
        INCLUDE_BOTH = 0x1,
        INCLUDE_ONLY_MUTANT = 0x2,
        INCLUDE_ONLY_WILDTYPE = 0x4,
        SPECIMEN_SELECTOR_HEIGHT = 220,
        SPECIMEN_SELECTOR_WIDTH = 300,
        STR_MUTANT = 'mutant',
        STR_WILDTYPE = 'wildtype',
        STR_IMAGE_PANEL = 'image-panel-',
        STR_IMAGE_PANEL_CLASS = '.' + STR_IMAGE_PANEL,
        STR_SPECIMEN_SELECTOR = 'specimen-selector-',
        STR_SPECIMEN_SELECTOR_CLASS = '.' + STR_SPECIMEN_SELECTOR,
        STR_VIEWPORT_CONTAINER = 'viewport-container-',
        STR_VIEWPORT_CONTAINER_CLASS = '.' + STR_VIEWPORT_CONTAINER,
        STR_LEFT = 'left',
        STR_RIGHT = 'right',
        STR_TOP = 'top',
        STR_BOTTOM = 'bottom',
        STR_ERROR = 'error',
        STR_WARNING = 'warning',
        STR_CONTROL_IS_ON = 'image-viewer-control-on',
        STR_LOADING = 'imageviewer-loading',
        STR_NO_IMAGES = 'imageviewer-no-images',
        THUMBNAIL_LIST_PAGE_SIZE = 100,
        /* to handle small screen */
        smallScreen = false,
        SMALL_SCREEN_WIDTH = 1300,
        EMBRYO_PROCESSING_PHASE = 99
        ;

    /**
     * Returns the current height of the DOM node.
     * 
     * @param {Object} node DOM node.
     * @param {Integer} value New height.
     * @returns {Integer} Height of the DOM node.
     */
    function dom_height(node, value) {
        if (typeof node === 'string')
            node = d3.select(node);
        if (value !== undefined)
            node.style('height', value + 'px');
        return node.node().getBoundingClientRect().height;
    }

    /**
     * Returns the current width of the DOM node.
     * 
     * @param {Object} node DOM node.
     * @param {Integer} value New height.
     * @returns {Integer} width of the DOM node.
     */
    function dom_width(node, value) {
        if (typeof node === 'string')
            node = d3.select(node);
        if (value !== undefined) {
            node.style('width', value + 'px');
        }
        return node.node().getBoundingClientRect().width;
    }

    /**
     * Returns the current left of the DOM node.
     * 
     * @param {Object} node DOM node.
     * @param {Integer} value New left.
     * @returns {Integer} width of the DOM node.
     */
    function dom_left(node, value) {
        if (typeof node === 'string')
            node = d3.select(node);
        if (value !== undefined)
            node.style(STR_LEFT, value + 'px');
        return parseInt(node.style(STR_LEFT), 10);
    }

    /**
     * Returns the current top of the DOM node.
     * 
     * @param {Object} node DOM node.
     * @param {Integer} value New top.
     * @returns {Integer} width of the DOM node.
     */
    function dom_top(node, value) {
        if (typeof node === 'string')
            node = d3.select(node);
        if (value !== undefined)
            node.style(STR_TOP, value + 'px');
        return parseInt(node.style(STR_TOP), 10);
    }

    /**
     * Returns the current right of the DOM node.
     * 
     * @param {Object} node DOM node.
     * @param {Integer} value New right.
     * @returns {Integer} width of the DOM node.
     */
    function dom_right(node, value) {
        if (typeof node === 'string')
            node = d3.select(node);
        if (value !== undefined)
            node.style(STR_RIGHT, value + 'px');
        return parseInt(node.style(STR_RIGHT), 10);
    }

    /**
     * Returns the current bottom of the DOM node.
     * 
     * @param {Object} node DOM node.
     * @param {Integer} value New bottom.
     * @returns {Integer} width of the DOM node.
     */
    function dom_bottom(node, value) {
        if (typeof node === 'string')
            node = d3.select(node);
        if (value !== undefined)
            node.style(STR_BOTTOM, value + 'px');
        return parseInt(node.style(STR_BOTTOM), 10);
    }

    /**
     * Returns the current padding of the DOM node.
     * 
     * @param {Object} node DOM node.
     * @param {String} which Which padding.
     * @param {Integer} value New top.
     * @returns {Integer} width of the DOM node.
     */
    function dom_padding(node, which, value) {
        if (typeof node === 'string')
            node = d3.select(node);
        switch (which) {
            case STR_LEFT:
            case STR_RIGHT:
            case STR_TOP:
            case STR_BOTTOM:
                which = 'padding-' + which;
                break;
            default:
                return undefined;
        }
        if (value !== undefined)
            node.style(which, value + 'px');
        return parseInt(node.style(which), 10);
    }

    /**
     * Returns the current margin of the DOM node.
     * 
     * @param {Object} node DOM node.
     * @param {String} which Which margin.
     * @param {Integer} value New top.
     * @returns {Integer} width of the DOM node.
     */
    function dom_margin(node, which, value) {
        if (typeof node === 'string')
            node = d3.select(node);
        switch (which) {
            case STR_LEFT:
            case STR_RIGHT:
            case STR_TOP:
            case STR_BOTTOM:
                which = 'margin-' + which;
                break;
            default:
                return undefined;
        }
        if (value !== undefined)
            node.style(which, value + 'px');
        return parseInt(node.style(which), 10);
    }

    /**
     * Creates a new DOM node.
     *
     * @param {Object} parent Parent DOM node to attach to.
     * @param {String} tag DOM node tag to use.
     * @param {String} id Identifier to use for the node.
     * @param {String} cls Style class for this node.
     * @param {String} text Text for inner HTML.
     */
    function createNode(parent, tag, id, cls, text) {
        return parent.append(tag)
            .attr('id', id)
            .attr('class', cls)
            .text(text);
    }

    function clear(node) {
        node.selectAll('*').remove();
    }

    /**
     * Appens a 'div' node with DOM identifier 'id' and class 'cls' as
     * a child under parent DOM node 'parent;.
     * 
     * @param {Object} parent Parent DOM node.
     * @param {String} id Identifier to use for child.
     * @param {String} cls Class to apply to child.
     * @param {String} text Text to put inside div.
     * @returns {Object} Child DOM node.
     */
    function addDiv(parent, id, cls, text) {
        var node = parent.append('div');
        if (id)
            node.attr('id', id);
        if (cls)
            node.attr('class', cls);
        if (text)
            node.text(text);
        return node;
    }

    /**
     * Checks if the node is visible inside the container node.
     * 
     * @param {Object} node DOM node.
     * @param {Object} container Containing DOM node.
     * @returns {Boolean} True if visible, otherwise false.
     */
    function isVisible(node, container) {
        var nodeDim = node.getBoundingClientRect(),
            containerDim = container.getBoundingClientRect();
        return !(nodeDim.top > containerDim.bottom ||
            nodeDim.bottom < containerDim.top ||
            nodeDim.left > containerDim.right ||
            nodeDim.right < containerDim.left);
    }

    /**
     * Prevent event from bubbling to parent DOM nodes.
     */
    function preventEventBubbling() {
        var event = d3.event;
        if (event) {
            if (event.preventDefault)
                event.preventDefault();
            if (event.stopPropagation)
                event.stopPropagation();
            event.cancelBubble = true;
        }
        return false;
    }

    /**
     * Throttles event handler so that it is not activated until
     * the supplied delay has passed.
     * 
     * @param {Function} method Function to call after delay.
     * @param {Integer} delay Number of millisconds to wait before method call.
     * @param {Object} thisArg What to pass as this to method.
     */
    function throttle(method, delay, thisArg) {
        clearTimeout(method.throttleTimeout);
        method.throttleTimeout = setTimeout(
            function () {
                method.apply(thisArg);
            }, delay);
    }

    /**
     * Transforms value to required precision. When precision is unspecified,
     * this uses 5 places of precision by default.
     *
     * @param {Real} value Value to transform.
     * @param {Integer} precision Places of precision.
     */
    function precision(value, precision) {
        return (value === undefined) ? undefined :
            value === 1 ? 1 :
            value.toPrecision(precision === undefined ? 5 : precision);
    }

    /**
     * Get the x-coordinate of mouse pointer relative to page.
     *
     * @param {type} event Mouse event.
     * @returns {Integer} x-coordinate of mouse relative to page in pixels.
     */
    function pageX(event) {
        return event.pageX === undefined ? event.clientX : event.pageX;
    }

    /**
     * Get the y-coordinate of mouse pointer relative to page.
     *
     * @param {type} event Mouse event.
     * @returns {Integer} y-coordinate of mouse relative to page in pixels.
     */
    function pageY(event) {
        return event.pageY === undefined ? event.clientY : event.pageY;
    }

    /**
     * Handles mouse event when user release a mouse button.
     */
    body.onmouseup = function () {
        mouseDown = false;
        isDragging = false;
        body.onselectstart = oldBodySelectStartHandler;
        if (oldBodyMouseUpHandler)
            oldBodyMouseUpHandler(d3.event);
    };

    var ThumbnailPager = function (obj) {
        this.parent = obj;
        this.pageSize = THUMBNAIL_LIST_PAGE_SIZE;
        this.currentPage = 0;
        this.lastPage = 0;
    };

    ThumbnailPager.prototype = {
        countActive: function (list, doInclude) {
            var i, c, k = 0;
            for (i = 0, c = list.length; i < c; ++i) {
                if (doInclude(list[i]))
                    k++;
            }
            return k;
        },
        hideInactiveButtons: function () {
            var me = this, parent = me.parent.thumbnailPagerContainer,
                temp = me.currentPage === me.lastPage,
                cls = 'disabled-pager-button';
            parent.select('.list-last-page').classed(cls, temp);
            parent.select('.list-next-page').classed(cls, temp);

            temp = me.currentPage === 0;
            parent.select('.list-first-page').classed(cls, temp);
            parent.select('.list-previous-page').classed(cls, temp);
        },
        refit: function () {

        },
        render: function (includeType) {
            var me = this, parentObj = me.parent, centering,
                container = parentObj.thumbnailPagerContainer,
                filter = parentObj.doInclude, list = parentObj.parent.data;

            clear(container);
            if (filter === undefined) {
                filter = function () {
                    return true;
                };
            }
            var numActiveRows = me.countActive(list, filter);
            me.lastPage = Math.ceil(numActiveRows / me.pageSize) - 1;
            centering = addDiv(container, null, 'list-pager-button-centering');
            addDiv(centering, null, 'list-first-page', 'first').on('click', function () {
                if (me.currentPage === 0)
                    return;
                me.currentPage = 0;
                fillSpecimen(parentObj, includeType);
            });
            addDiv(centering, null, 'list-previous-page', 'previous').on('click', function () {
                if (me.currentPage === 0)
                    return;
                --me.currentPage;
                fillSpecimen(parentObj, includeType);
            });
            addDiv(centering, null, 'list-page-count', (me.currentPage + 1) + '/' + (me.lastPage + 1));
            addDiv(centering, null, 'list-next-page', 'next').on('click', function () {
                if (me.currentPage === me.lastPage)
                    return;
                ++me.currentPage;
                fillSpecimen(parentObj, includeType);
            });
            addDiv(centering, null, 'list-last-page', 'last').on('click', function () {
                if (me.currentPage === me.lastPage)
                    return;
                me.currentPage = me.lastPage;
                fillSpecimen(parentObj, includeType);
            });
            me.hideInactiveButtons();
            return numActiveRows;
        }
    };

    /**
     * Implements a value slider user interface.
     *
     * @param {Object} parent Container node.
     * @param {String} id Unique identifier for the slider.
     * @param {String} label The value label.
     * @param {Integer} height Maximum height for the slider in pixels.
     * @param {Integer} width Maximum width for the slider in pixels.
     * @param {Function} onValueChange Processing to do when value changes.
     * @param {Real} values Allowed slider values.
     * @param {Real} defaultValue Optional default value.
     */
    var Slider = function (parent, id, label, height,
        width, onValueChange, values, defaultValue) {
        this.id = id;
        values.sort(function (a, b) {
            return a < b ? -1 : a > b ? 1 : 0;
        });
        this.values = values;
        this.minValue = values[0];
        this.maxValue = values[values.length - 1];
        this.valueRange = this.maxValue - this.minValue;
        if (values.length > 2)
            this.isSnapping = true;
        this.setDefaultValue(defaultValue);
        this.onValueChange = onValueChange;
        this.sliderHeight = height;
        this.sliderWidth = width;
        this.labelText = label;
        this.renderSlider(parent);
    };
    Slider.prototype = {
        /**
         * Returns the index and value after snapping the supplied value
         * to the closest value in the list of values.
         * 
         * @param {Real} value Supplied value to snap.
         * @returns {Object} Index and snapped value.
         */
        getSnapValue: function (value) {
            var me = this, values = me.values, i, c = values.length - 1;
            for (i = 0; i < c; ++i)
                if (values[i] <= value && value < values[i + 1])
                    break;
            if (i === c && value > values[i])
                i = Math.floor(0.5 * values.length);
            return {
                'index': i,
                'value': values[i]
            };
        },
        /**
         * Returns non-snapping value within the bounds.
         * 
         * @param {Real} value Supplied value.
         * @returns {Real} Value within bounds.
         */
        getNonsnapValue: function (value) {
            var me = this;
            if (value === undefined
                || value < me.minValue
                || value > me.maxValue)
                value = 0.5 * me.valueRange;
            return value;
        },
        /**
         * Set the default value to use when the supplied slider value is
         * undefined or out-of-bounds.
         * 
         * @param {type} value Supplied value to set the slider to.
         */
        setDefaultValue: function (value) {
            var me = this, temp;
            if (me.isSnapping) {
                temp = me.getSnapValue(value);
                me.defaultValueIndex = temp.index;
                me.defaultValue = temp.value;
            } else
                this.defaultValue = me.getNonsnapValue(value);
        },
        /**
         * Increase or decrease the value index by increasing the current
         * value index by supplied delta. This will also update the current
         * slider value. This is only effective when the slider is in
         * snapping value more.
         * 
         * @param {type} delta Integer increment or decrement value.
         */
        updateValueIndex: function (delta) {
            var me = this, values = me.values, index;
            if (me.isSnapping) {
                index = me.valueIndex;
                if (index === undefined)
                    index = me.defaultValueIndex;
                else {
                    index += delta;
                    if (index < 0)
                        index = 0;
                    else if (index > values.length - 1)
                        index = values.length - 1;
                }
                if (me.valueIndex !== index) {
                    me.valueIndex = index;
                    me.activateSliderValueChange(values[index]);
                }
            }
        },
        /**
         * Sets slider value and position of the slider button.
         * 
         * @param {Real} value New value for the slider.
         */
        setSliderValue: function (value) {
            var me = this, temp;
            if (value === undefined) {
                if (me.isSnapping)
                    me.valueIndex = me.defaultValueIndex;
                value = me.defaultValue;
            } else {
                if (me.isSnapping) {
                    temp = me.getSnapValue(value);
                    me.valueIndex = temp.index;
                    value = temp.value;
                } else
                    value = me.getNonsnapValue(value);
            }
            me.activateSliderValueChange(value);
        },
        activateSliderValueChange: function (value) {
            var me = this;
            me.value.node().value = value;
            me.buttonLeft = me.positionFromValue();
            dom_left(me.button, me.buttonLeft);
            me.onValueChange(value);
        },
        getSliderValue: function () {
            var me = this, currentValue = me.value.node().value;
            if (floatingPointRegEx.test(currentValue))
                currentValue = parseFloat(currentValue);
            else
                console.log('Invalid value');
            return currentValue;
        },
        /**
         * Converts current slider value to slider button position.
         * This is used for updating the position of the slider button when
         * user updates the value text box.
         */
        positionFromValue: function () {
            var me = this, valueBox = me.value, value = valueBox.node().value;
            if (floatingPointRegEx.test(value)) {
                valueBox.style('color', '#000000'); /* valid value */

                /* keep value within range */
                if (value < me.minValue) {
                    value = me.minValue;
                    /* value is less than min, show warning with colour */
                    valueBox.style('color', 'green');
                } else if (value > me.maxValue) {
                    value = me.maxValue;
                    /* value is more than max, show warning with colour */
                    valueBox.style('color', 'blue');
                }
            } else {
                valueBox.style('color', '#ff0000'); /* highlight error */
                value = me.defaultValue;
            }

            return me.minButtonLeft + me.barWidth
                * (value - me.minValue) / me.valueRange; /* lerp */
        },
        /**
         * Converts current slider button position to slider value.
         * This is used for updating the slider value when the user drags the
         * slider button.
         */
        valueFromPosition: function () {
            var me = this, values, value, i, valueIndex;
            me.value.style('color', '#000000');
            value = me.minValue + me.valueRange * (dom_left(me.button)
                + .5 * me.buttonWidth - me.barLeft) / me.barWidth; /* lerp */
            if (me.isSnapping) {
                values = me.values;
                valueIndex = values.length - 1;
                for (i = 0; i < valueIndex; ++i)
                    if (values[i] <= value && value < values[i + 1]) {
                        valueIndex = i;
                        break;
                    }
                me.valueIndex = valueIndex;
                value = values[valueIndex];
            }
            return precision(value);
        },
        /**
         * This event handler is invoked when the user begins dragging the
         * slider button.
         * 
         * @param {Object} button Event is attached to the button DOM node.
         */
        getDragStartHandler: function (button) {
            return function () {
                preventEventBubbling();
                mouseDown = true;
                button.displacement = dom_left(button) - pageX(d3.event);
                /* prevent selection event when dragging */
                body.onselectstart = function () {
                    return false;
                };
            };
        },
        /**
         * This event handler is invoked when the user continues dragging
         * the slider button.
         * 
         * @param {Object} button Event is attached to the button DOM node.
         */
        getDragHandler: function (button) {
            var me = this;
            return function () {
                preventEventBubbling();
                if (mouseDown) {
                    var newPosition = pageX(d3.event) + button.displacement,
                        oldValue, newValue;
                    /* keep slider button within range */
                    if (newPosition >= me.minButtonLeft
                        && newPosition <= me.maxButtonRight) {
                        dom_left(button, newPosition);
                        oldValue = me.value.node().value;
                        newValue = me.valueFromPosition();
                        if (oldValue !== newValue) {
                            me.value.node().value = newValue;
                            if (me.onValueChange)
                                me.onValueChange();
                        }
                    }
                }
            };
        },
        /**
         * Attaches events for implementing dragging event on slider button.
         */
        attachSliderDragHandler: function () {
            var me = this, sliderRegion = me.range, button = me.button,
                dragStart = me.getDragStartHandler(button),
                drag = me.getDragHandler(button);
            /* dragging event begins when user clicks on the slider button. */
            button.on('touchstart', dragStart);
            button.on('mousedown', dragStart);
            /* dragging continues when user moves the mouse over the slider
             * region when the mouse button is depressed. */
            sliderRegion.on('touchmove', drag);
            sliderRegion.on('mousemove', drag);
            sliderRegion.on('mouseup', function () {
                preventEventBubbling();
                mouseDown = false;
                isDragging = false;
            });
        },
        /**
         * The slider dimensions must be set based on the size of the labels,
         * supplied slider styling etc. Hence, these are calculated dynamically
         * after the components have been rendered.
         */
        refitSlider: function () {
            var me = this,
                /* vertical middle of the slider component */
                midHeight = me.sliderHeight * .5,
                /* label dimensions */
                labelWidth = dom_width(me.label),
                labelHeight = dom_height(me.label),
                labelTop = midHeight - labelHeight * .5,
                /* value box dimensions */
                valueHeight = dom_height(me.value)
                + dom_padding(me.value, STR_TOP)
                + dom_padding(me.value, STR_BOTTOM),
                valueTop = midHeight - valueHeight * .5,
                resetWidth = dom_width(me.reset),
                minWidth = dom_width(me.min),
                maxWidth = dom_width(me.max),
                /* range contains the bar, button, and min and max labels */
                rangeWidth = me.sliderWidth - labelWidth - resetWidth,
                rangeTop = 0,
                rangeHeight = me.sliderHeight,
                /* horizontal bar dimensions */
                barWidth = rangeWidth - minWidth - maxWidth,
                barHeight = dom_height(me.bar),
                barTop = midHeight - barHeight * .5,
                barLeft = minWidth,
                /* slider button dimensions */
                buttonHeight = dom_height(me.button),
                buttonTop = midHeight - buttonHeight * .5,
                /* min label dimensions */
                minTop = midHeight - 9,
                minLeft = barLeft - minWidth,
                /* max label dimensions */
                maxTop = minTop,
                maxLeft = barLeft + barWidth;
            /* the following values are used when converting slider value to
             * button position, and vice versa */
            me.buttonWidth = dom_width(me.button);
            me.halfButtonWidth = .5 * me.buttonWidth;
            me.barLeft = barLeft;
            me.barRight = barLeft + barWidth;
            me.barWidth = barWidth;
            me.minButtonLeft = barLeft - me.halfButtonWidth;
            me.maxButtonRight = me.barRight - me.halfButtonWidth;
            /* using the dimensions just calculated, resize components */
            dom_width(me.slider, me.sliderWidth);
            dom_height(me.slider, me.sliderHeight);
            dom_top(me.label, labelTop);
            dom_top(me.value, valueTop);
            dom_top(me.range, rangeTop);
            dom_width(me.range, rangeWidth);
            dom_height(me.range, rangeHeight);
            dom_top(me.bar, barTop);
            dom_width(me.bar, barWidth);
            dom_left(me.bar, barLeft);
            dom_top(me.button, buttonTop);
            dom_width(me.button, me.buttonWidth);
            dom_top(me.min, minTop);
            dom_left(me.min, minLeft);
            dom_top(me.max, maxTop);
            dom_left(me.max, maxLeft);
            me.setSliderValue();
            return me;
        },
        /**
         * Render the components of the slider by adding DOM nodes for each of
         * the components. Note that the identifier for each of the components
         * are derived from the slider identifier.
         *
         * @param {Object} parent Parent DOM nodes that contains the slider.
         */
        renderSlider: function (parent) {
            var me = this, id = me.id, prefix = 'dcc-slider';
            /* contains the entire slider */
            me.slider = createNode(parent, 'div', id, prefix);
            /* slider label */
            me.label = createNode(me.slider, 'div',
                id + '-label', prefix + '-label', me.labelText);
            /* editable slider value box */
            me.value = createNode(me.slider, 'input',
                id + '-value', prefix + '-value');
            /**
             * Attach event handler that updates slider button position when the
             * value in this box changes. */
            me.value.on('keyup', function () {
                me.setSliderValue(me.value.node().value);
            });
            /* important to call this after attaching the event above */
            me.value.node().value = me.defaultValue;
            /* range contains the bar, button, and min and max labels */
            me.range = createNode(me.slider, 'div',
                id + '-range', prefix + '-range');
            me.bar = createNode(me.range, 'div',
                id + '-bar', prefix + '-bar');
            me.button = createNode(me.range, 'div',
                id + '-button', prefix + '-button');
            /* resets the p-value threshold to default value */
            me.reset = createNode(me.slider, 'div',
                id + '-reset', prefix + '-reset');
            me.reset.attr('title', 'Reset slider value');
            me.reset.on('click', function () {
                me.setSliderValue();
            });
            me.min = createNode(me.range, 'div',
                id + '-min', prefix + '-min', me.minValue);
            me.max = createNode(me.range, 'div',
                id + '-max', prefix + '-max', me.maxValue);
            me.refitSlider();
            me.attachSliderDragHandler(me);
            me.onValueChange(me.value.value);
            return me;
        },
        hideSlider: function () {
            this.slider.style('visibility', 'hidden');
        },
        showSlider: function () {
            this.slider.style('visibility', 'visible');
        }
    };

    function getControlSyncHandler(parent) {
        return function (config) {
            var comparative = parent.viewport.parent.parent;
            if (comparative.panel === undefined) {
                if (comparative.mutantPanel.viewer.title === parent.title)
                    comparative.wildtypePanel.viewer.setControl(config);
                else
                    comparative.mutantPanel.viewer.setControl(config);
            }
        };
    }

    function getZoomHandler(parent) {
        return function () {
            preventEventBubbling();
            var scale = this.zoomSlider.getSliderValue(),
                regionOfInterest = parent.regionOfInterest;
            if (regionOfInterest)
                regionOfInterest.resize();
            parent.viewport.scale(scale);
            if (syncControls) {
                var handler = getControlSyncHandler(parent);
                handler({
                    'zoom': scale
                });
            }
        };
    }

    function forceRenderingOfAllCanvases(viewport) {
        viewport.selectAll('canvas').each(function () {
            this.isRendered = undefined;
        });
    }

    function getBrightnessHandler(parent) {
        return function () {
            preventEventBubbling();
            forceRenderingOfAllCanvases(parent.viewportContainer);
            parent.imageProcessingConfig.brightness =
                this.brightnessSlider.getSliderValue();
            parent.viewport.refresh();
            if (syncControls) {
                var handler = getControlSyncHandler(parent);
                handler({
                    'brightness': parent.imageProcessingConfig.brightness
                });
            }
        };
    }

    function getContrastHandler(parent) {
        return function () {
            preventEventBubbling();
            forceRenderingOfAllCanvases(parent.viewportContainer);
            parent.imageProcessingConfig.contrast =
                this.contrastSlider.getSliderValue();
            parent.viewport.refresh();
            if (syncControls) {
                var handler = getControlSyncHandler(parent);
                handler({
                    'contrast': parent.imageProcessingConfig.contrast
                });
            }
        };
    }

    function getToggleColourInversion(parent) {
        return function () {
            preventEventBubbling();
            parent.imageProcessingConfig.invert =
                !parent.imageProcessingConfig.invert;
            forceRenderingOfAllCanvases(parent.viewportContainer);
            parent.viewport.refresh();
            if (syncControls) {
                var handler = getControlSyncHandler(parent);
                handler({
                    'invert': parent.imageProcessingConfig.invert
                });
            }
        };
    }

    function getToggleChannel(parent, channel) {
        return function () {
            preventEventBubbling();
            parent.imageProcessingConfig[channel] =
                !parent.imageProcessingConfig[channel];
            forceRenderingOfAllCanvases(parent.viewportContainer);
            parent.viewport.refresh();
            if (syncControls) {
                var handler = getControlSyncHandler(parent), config = {};
                config[channel] = parent.imageProcessingConfig[channel];
                handler(config);
            }
        };
    }

    function ViewControl(obj) {
        this.parent = obj;
        this.viewport = obj.viewport;
        this.container = obj.viewportContainer;
        this.scales = obj.scales;
        this.init();
    }

    function addCheckbox(container, label, handler, defaultValue) {
        var checkbox = container.append('div')
            .attr('class', 'image-processing-checkbox')
            .text(label)
            .on('click', function () {
                checkbox.classed('checked', !checkbox.classed('checked'));
                if (handler)
                    handler();
            });
        if (defaultValue !== undefined)
            checkbox.classed('checked', defaultValue);
        return checkbox;
    }

    ViewControl.prototype = {
        init: function () {
            var me = this, parent = me.parent,
                container = me.container, temp,
                zoomHandler = getZoomHandler(parent),
                brightnessHandler = getBrightnessHandler(parent),
                contrastHandler = getContrastHandler(parent),
                toggleColourInversion = getToggleColourInversion(parent),
                toggleRedChannel = getToggleChannel(parent, 'red'),
                toggleBlueChannel = getToggleChannel(parent, 'blue'),
                toggleGreenChannel = getToggleChannel(parent, 'green');

            me.node = container.append('div')
                .attr('id', 'view-control-' + parent.id)
                .attr('class', 'view-control unselectable');

            me.zoomSlider = new Slider(me.node,
                'zoom-slider', 'Zoom:', 26, 420,
                function () {
                    throttle(zoomHandler, 10, me);
                }, me.scales, 25);

            me.brightnessSlider = new Slider(me.node,
                'brightness-slider', 'Brightness:', 26, 420,
                function () {
                    throttle(brightnessHandler, 10, me);
                }, [-1.0, 1.0], 0.0);

            me.contrastSlider = new Slider(me.node,
                'contrast-slider', 'Contrast:', 26, 420,
                function () {
                    throttle(contrastHandler, 10, me);
                }, [0, 3.0], 1.0);

            me.events();
            temp = me.node.append('div').attr('class', 'checkbox-container');
            me.invertColorCheckbox = addCheckbox(temp, 'Invert colour',
                toggleColourInversion, false);
            me.redChannelCheckbox = addCheckbox(temp, 'Red',
                toggleRedChannel, true);
            me.greenChannelCheckbox = addCheckbox(temp, 'Green',
                toggleGreenChannel, true);
            me.blueChannelCheckbox = addCheckbox(temp, 'Blue',
                toggleBlueChannel, true);
        },
        getControl: function () {
            var me = this;
            return {
                'zoom': me.zoomSlider.getSliderValue(),
                'brightness': me.brightnessSlider.getSliderValue(),
                'contrast': me.contrastSlider.getSliderValue()
            };
        },
        setControl: function (config) {
            var me = this, checkbox, checked;
            if (config) {
                if (config.zoom !== undefined
                    && config.zoom !== me.zoomSlider.getSliderValue()) {
                    me.zoomSlider.setSliderValue(config.zoom);
                }
                if (config.brightness !== undefined && config.brightness !==
                    me.brightnessSlider.getSliderValue()) {
                    me.brightnessSlider.setSliderValue(config.brightness);
                }
                if (config.contrast !== undefined
                    && config.contrast !== me.contrastSlider.getSliderValue()) {
                    me.contrastSlider.setSliderValue(config.contrast);
                }
                if (config.invert !== undefined) {
                    checkbox = me.invertColorCheckbox;
                    checked = checkbox.classed('checked');
                    if ((config.invert && !checked) ||
                        (!config.invert && checked))
                        checkbox.on("click")();
                }
                if (config.red !== undefined) {
                    checkbox = me.redChannelCheckbox;
                    checked = checkbox.classed('checked');
                    if ((config.red && !checked) ||
                        (!config.red && checked))
                        checkbox.on("click")();
                }
                if (config.green !== undefined) {
                    checkbox = me.greenChannelCheckbox;
                    checked = checkbox.classed('checked');
                    if ((config.green && !checked) ||
                        (!config.green && checked))
                        checkbox.on("click")();
                }
                if (config.blue !== undefined) {
                    checkbox = me.blueChannelCheckbox;
                    checked = checkbox.classed('checked');
                    if ((config.blue && !checked) ||
                        (!config.blue && checked))
                        checkbox.on("click")();
                }
            }
        },
        refit: function () {
            var me = this;
            me.controlWidth = dom_width(me.node);
            me.controlHeight = dom_height(me.node);
            me.containerWidth = dom_width(me.container);
            me.containerHeight = dom_height(me.container);
        },
        bound_right_bottom: function (right, bottom) {
            var me = this,
                minRight = me.containerWidth - me.controlWidth,
                minBottom = me.containerHeight - me.controlHeight;
            if (right > minRight)
                right = minRight;
            else if (right < 0)
                right = 0;
            if (bottom > minBottom)
                bottom = minBottom;
            else if (bottom < 0)
                bottom = 0;
            return {
                'r': right,
                'b': bottom
            };
        },
        bound_left_top: function (left, top) {
            var me = this,
                maxLeft = me.containerWidth - me.controlWidth,
                maxTop = me.containerHeight - me.controlHeight;
            if (left < 0)
                left = 0;
            else if (left >= maxLeft)
                left = maxLeft;
            if (top < 0)
                top = 0;
            else if (top >= maxTop)
                top = maxTop;
            return {
                'l': left,
                't': top
            };
        },
        events: function () {
            var me = this, node = me.node;
            node.on('mousedown', function () {
                preventEventBubbling();
                if (!isDragging) {
                    isDragging = true;
                    node.classed('grabbing', true).classed('grab', false);
                    var coord = d3.mouse(this.parentNode);
                    dragX = coord[0];
                    dragY = coord[1];
                }
            });
            node.on('mousemove', function () {
                preventEventBubbling();
                if (isDragging) {
                    var coord = d3.mouse(this.parentNode),
                        dx = dragX - coord[0], dy = dragY - coord[1],
                        rightBottom = me.bound_right_bottom(dom_right(node) + dx, dom_bottom(node) + dy);
                    dom_right(node, rightBottom.r);
                    dom_bottom(node, rightBottom.b);
                    dragX = coord[0];
                    dragY = coord[1];
                }
            });
            node.on('mouseup', function () {
                preventEventBubbling();
                if (isDragging) {
                    node.classed('grabbing', false).classed('grab', true);
                    isDragging = false;
                }
            });
        },
        width: function () {
            var me = this;
            return dom_width(me.node);
        },
        height: function () {
            var me = this;
            return dom_height(me.node);
        },
        scale: function (delta) {
            var me = this;
            me.zoomSlider.updateValueIndex(delta);
        },
        getScale: function () {
            var me = this;
            return me.zoomSlider.getSliderValue();
        }
    };

    function Viewport(obj) {
        this.parent = obj;
        this.init();
    }
    Viewport.prototype = {
        init: function () {
            var me = this, parent = me.parent, id = parent.id,
                container = parent.viewportContainer;
            me.node = container.append('div')
                .attr('id', 'viewport-' + id)
                .attr('class', 'viewport')
                .classed('grab', true);
            me.layers = [];
            me.layerStack = me.node.append('div')
                .attr('id', 'layerstack-' + id);
            me.events();
        },
        d3node: function () {
            var me = this;
            return me.node;
        },
        width: function () {
            var me = this;
            return dom_width(me.node);
        },
        scale: function (percentage) {
            var me = this, layer, layers = me.layers, parent = me.parent;
            for (layer in me.layers)
                layers[layer].scale(percentage);
            if (parent.regionOfInterest) {
                layer = layers[0];
                parent.regionOfInterest.move(layer.left(), layer.top());
            }
        },
        refresh: function () {
            var me = this, layer, layers = me.layers;
            for (layer in me.layers)
                layers[layer].refresh();
        },
        refit: function () {
            var me = this, layer, layers = me.layers;
            for (layer in me.layers)
                layers[layer].refit();
        },
        getScale: function () {
            var me = this, parent = me.parent;
            return parent.viewControl.getScale();
        },
        height: function () {
            var me = this;
            return dom_height(me.node);
        },
        drag: function (dx, dy) {
            var me = this, layer, layers = me.layers, parent = me.parent;
            for (layer in me.layers)
                layers[layer].displace(dx, dy);
            if (parent.regionOfInterest) {
                layer = layers[0];
                parent.regionOfInterest.move(layer.left(), layer.top());
            }
        },
        displace: function (dx, dy) {
            var me = this, layer, layers = me.layers;
            for (layer in me.layers)
                layers[layer].displace(dx, dy);
        },
        move: function (left, top) {
            var me = this, layer, layers = me.layers;
            for (layer in me.layers)
                layers[layer].move(left, top);
        },
        left: function () {
            var me = this, l = 0;
            if (me.layers.length > 0)
                l = me.layers[0].left();
            return l;
        },
        top: function () {
            var me = this, t = 0;
            if (me.layers.length > 0)
                t = me.layers[0].top();
            return t;
        },
        empty: function () {
            var me = this;
            me.layerStack.selectAll('div').remove();
            me.layers = [];
        },
        add: function (layer) {
            var me = this;
            me.layers.push(layer);
        },
        events: function () {
            var me = this, node = me.layerStack, parent = me.parent;
            node.on('mousedown', function () {
                preventEventBubbling();
                if (!isDragging) {
                    isDragging = true;
                    node.classed('grabbing', true).classed('grab', false);
                    var coord = d3.mouse(this);
                    dragX = coord[0];
                    dragY = coord[1];
                }
            });
            node.on('mousemove', function () {
                preventEventBubbling();
                if (isDragging) {
                    var coord = d3.mouse(this);
                    me.drag(dragX - coord[0], dragY - coord[1]);
                    dragX = coord[0];
                    dragY = coord[1];
                }
            });
            node.on('mouseup', function () {
                preventEventBubbling();
                if (isDragging) {
                    me.layerStack
                        .classed('grabbing', false)
                        .classed('grab', true);
                    isDragging = false;
                }
            });
            var mousewheelEventName = (/Firefox/i.test(navigator.userAgent))
                ? "DOMMouseScroll" : "mousewheel";
            me.node.on(mousewheelEventName, function () {
                preventEventBubbling();
                var e = d3.event, delta = Math.max(-1, Math.min(1,
                    (e.wheelDelta || -e.detail)));
                parent.viewControl.scale(delta);
            });
        }
    };

    function Layer(obj, params) {
        this.viewer = obj;
        if (params !== undefined) {
            this.viewport = params.viewport;
            this.opacity = params.opacity;
            this.percentage = params.scale;
        }
        this.init();
    }
    ;
    Layer.prototype = {
        init: function () {
            var me = this;
            me.node = me.viewport.layerStack.append('div')
                .attr('id', 'layer-' + me.viewer.id)
                .attr('class', 'layer')
                .style('opacity', me.opacity);
        },
        scale: function (percentage) {
            var me = this, content = me.content;
            if (content !== undefined) {
                var dim = content.scale(percentage);
                me.height = dim.height;
                me.width = dim.width;
                me.contentHeight = dim.contentHeight;
                me.contentWidth = dim.contentWidth;
                dom_width(me.node, me.width);
                dom_height(me.node, me.height);
                me.center();
                content.refresh();
            }
        },
        refresh: function () {
            var me = this, content = me.content;
            if (content !== undefined)
                content.refresh();
        },
        refit: function () {
            var me = this, content = me.content;
            if (content !== undefined) {
                me.center();
                content.refresh();
            }
        },
        center: function () {
            var me = this, viewport = me.viewport;
            dom_top(me.node, (viewport.height() - me.contentHeight) * 0.5);
            dom_left(me.node, (viewport.width() - me.contentWidth) * 0.5);
        },
        getViewport: function () {
            var me = this;
            return me.viewport;
        },
        add: function (content) {
            var me = this;
            me.content = content;
            me.scale(me.percentage);
        },
        d3node: function () {
            var me = this;
            return me.node;
        },
        displace: function (dx, dy) {
            var me = this, node = me.node,
                l = dom_left(node) - dx, t = dom_top(node) - dy;
            if (l <= 0 && l > me.viewport.width() - me.contentWidth)
                dom_left(node, l);
            if (t <= 0 && t > me.viewport.height() - me.contentHeight)
                dom_top(node, t);
            me.content.refresh();
        },
        move: function (left, top) {
            var me = this, node = me.node;
            if (left <= 0 && left > me.viewport.width() - me.contentWidth)
                dom_left(node, left);
            if (top <= 0 && top > me.viewport.height() - me.contentHeight)
                dom_top(node, top);
            me.content.refresh();
        },
        left: function () {
            var me = this;
            return dom_left(me.node);
        },
        top: function () {
            var me = this;
            return dom_top(me.node);
        }
    };

    function ImageTileGrid(obj, params) {
        this.viewer = obj;
        if (params !== undefined) {
            this.tileSize = params.tileSize;
            this.server = params.server;
            this.checksum = params.checksum;
            this.width = params.width;
            this.height = params.height;
            this.percentage = params.scale;
            this.layer = params.layer;
        }
        this.init();
    }

    ImageTileGrid.prototype = {
        getTilesUrl: function () {
            var me = this;
            return me.server + me.checksum
                + me.tileSize + '/' + me.percentage
                + '/' + me.numCols + '_' + me.numRows + '_';
        },
        init: function () {
            var me = this;
            me.grid = me.layer.d3node().append('div')
                .attr('class', 'tiles-grid');
            me.viewport = me.layer.getViewport();
            me.scale(me.percentage);
        },
        scale: function (percentage) {
            var me = this, factor, tileScale, scaledHeight, scaledWidth;
            if (!(percentage < 0 || percentage > 100)) {
                me.percentage = percentage;
                factor = percentage * 0.01;
                scaledHeight = me.height * factor;
                scaledWidth = me.width * factor;
                tileScale = factor / me.tileSize;
                me.numRows = Math.ceil(me.height * tileScale);
                me.numCols = Math.ceil(me.width * tileScale);
                me.tilesUrl = me.getTilesUrl();
                me.render();
                return {
                    'width': me.numCols * me.tileSize,
                    'height': me.numRows * me.tileSize,
                    'contentWidth': scaledWidth,
                    'contentHeight': scaledHeight
                };
            }
        },
        render: function () {
            var me = this, i, j, r, c, tile, node,
                grid = me.grid, tileSize = me.tileSize;
            grid.selectAll('canvas').remove();
            for (i = 0, r = me.numRows; i < r; ++i)
                for (j = 0, c = me.numCols; j < c; ++j) {
                    tile = grid.append('canvas')
                        .style('float', STR_LEFT)
                        .attr('width', tileSize)
                        .attr('height', tileSize);
                    node = tile.node();
                    node.i = i;
                    node.j = j;
                }
        },
        refresh: function () {
            var me = this, tileSize = me.tileSize, tilesUrl = me.tilesUrl,
                config = me.viewer.imageProcessingConfig,
                viewport = me.viewport.d3node().node();
            me.grid.selectAll('canvas')
                .each(function (d) {
                    var url, canvas = this;
                    if (isVisible(canvas, viewport)
                        && canvas.isRendered === undefined) {
                        canvas.isRendered = true;
                        url = tilesUrl + this.i + '_' + this.j
                            + PREFERRED_IMAGE_FORMAT;
                        prepareCanvas(canvas, tileSize, url, config);
                    }
                });
        }
    };

    function prepareCanvas(canvas, tileSize, url, config) {
        var img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = function () {
            var context = canvas.getContext('2d');
            if (this.width !== tileSize || this.height !== tileSize) {
                context.fillStyle = '#000';
                context.fillRect(0, 0, tileSize, tileSize);
            }
            context.drawImage(img, 0, 0);
            canvas.imgData = context.getImageData(0, 0, this.width, this.height);
            canvas.context = context;
            renderImage(canvas, config);
        };
        img.src = url;
    }

    function renderImage(canvas, config) {
        var data = canvas.imgData, context = canvas.context;
        data.data = processPixels(data.data, config);
        context = context.putImageData(data, 0, 0);
    }

    function processPixels(data, config) {
        if (config.invert)
            invertColour(data);
        brightnessContrast(data, config);
        if (!config.red)
            hideChannel(data, 0);
        if (!config.green)
            hideChannel(data, 1);
        if (!config.blue)
            hideChannel(data, 2);
    }

    function invertColour(data) {
        for (var i = 0, c = data.length; i < c; i += 4) {
            data[i] = 255 - data[i];
            data[i + 1] = 255 - data[i + 1];
            data[i + 2] = 255 - data[i + 2];
            data[i + 3] = 255;
        }
    }

    function hideChannel(data, channelOffset) {
        for (var i = 0, c = data.length; i < c; i += 4)
            data[i + channelOffset] = 0;
    }

    /* http://pippin.gimp.org/image_processing/chap_point.html */
    function brightnessContrast(data, config) {
        var i, c, j, k, contrast = config.contrast * 255,
            term = (0.5 + config.brightness) * 255;
        for (i = 0, c = data.length; i < c; i += 4)
            for (j = i, k = i + 3; j < k; ++j)
                data[j] = (data[j] / 255 - 0.5) * contrast + term;
    }

    function getPathFromChecksum(checksum) {
        return checksum.replace(/(.{4})/g, "$1\/");
    }

    function addImageTileLayer(image, obj) {
        var id = image.id, viewport = obj.viewport,
            scale = viewport.getScale(),
            width = image.w, height = image.h,
            layer = new Layer(obj, {
                'viewport': viewport,
                'width': width,
                'height': height,
                'opacity': 1,
                'scale': scale
            });
        viewport.add(layer);
        layer.add(new ImageTileGrid(obj, {
            'tileSize': TILE_SIZE,
            'server': IMAGE_TILE_SERVER,
            'checksum': getPathFromChecksum(image.c),
            'width': width,
            'height': height,
            'layer': layer,
            'scale': scale
        }));
        return layer;
    }

    function replaceImageTileLayer(image, obj) {
        obj.viewport.empty();
        return addImageTileLayer(image, obj);
    }

    function getQueryParam(context, includeBaseline) {
        var temp = '?cid=' + context.cid +
            '&gid=' + context.gid +
            '&sid=' + context.sid +
            '&qeid=' + context.qeid;
        if (context.pid)
            temp += '&pid=' + context.pid;
        if (context.lid)
            temp += '&lid=' + context.lid;
        if (includeBaseline)
            temp += '&includeBaseline=true';
        return temp;
    }

    function getThumbnailUrl(image) {
        return IMAGE_TILE_SERVER + getPathFromChecksum(image.c) +
            'thumbnail' + PREFERRED_IMAGE_FORMAT;
    }

    function getMediaUrl(media, context) {
        return ORIGINAL_MEDIA_SERVER + context.cid + '/' +
            media.lid + '/' +
            media.gid + '/' +
            context.sid + '/' +
            media.pid + '/' +
            media.qid + '/' + media.id + '.' + media.e;
    }

    function getEmbryoMediaUrl(media, context) {
        return EMBRYO_MEDIA_SERVER + context.cid + '/' +
            media.lid + '/' +
            media.gid + '/' +
            context.sid + '/' +
            media.pid + '/' +
            media.qid + '/' + media.id + '_';
    }

    function getImageSelectionHandler(obj, image, roi) {
        var viewport = obj.viewport;
        return function () {
            preventEventBubbling();
            var node = d3.select(this), parent = d3.select(this.parentNode);
            parent.selectAll('.active').classed('active', false);
            node.classed('active', true);

            replaceImageTileLayer(image, obj);
            if (roi.scale !== viewport.getScale())
                roi.resize();
            roi.move(viewport.left(), viewport.top());
            obj.regionOfInterest = roi;
            if (obj.download)
                obj.download.attr('href', getMediaUrl(image, obj.context));
            if (image.l) {
                obj.external.attr('href', image.l).style('display', 'block');
            } else {
                obj.external.style('display', 'none');
            }
            obj.mediaTitle = getMediaTitle(image);
            obj.mediaShortTitle = getMediaTitle(image, true);
            if (obj.specimenTitle)
                obj.specimenTitle.html(smallScreen ? obj.mediaShortTitle : obj.mediaTitle);
            this.scrollIntoView(true);
            dcc.mediaContextForQC = image;
        };
    }

    function replacePdfIframe(viewport, url) {
        var iframe;
        viewport.selectAll('*').remove();
        iframe = viewport.append('iframe')
            .attr('src', url)
            .attr('frameborder', 0);
    }

    var views = ['sagittal', 'coronal', 'axial'];
    function replaceEmbryoImage(media, viewport, url) {
        var i, view, node, title, img, height, width;
        viewport.selectAll('*').remove();
        height = dom_height(viewport);
        width = dom_width(viewport);
        /* embryo processing successful */
        if (media.s === 1) {
            for (i in views) {
                view = views[i];
                node = viewport.append('div').attr('class', 'embryo-view');
                title = node.append('div').attr('class', 'title').text(view);

                img = node.append('img')
                    .attr('class', view)
                    .attr('src', url + view + '.png')
                    .on('error', function () {
                        var parent = d3.select(this.parentNode);
                        parent.selectAll('img').remove();
                        parent.append('div')
                            .attr('class', 'no-image')
                            .text('Image unavailable');
                    });
                // 6 pixels for the border.
                if (height > width) {
                    dom_width(img, Math.floor(width / 3) - 6);
                } else {
                    // TODO: we should resize properly; but this is enought for now.
                    dom_height(img, height - dom_height(title) - 6);
                }
            }
            viewport.style('overflow', 'auto');
        } else {
            viewport.append('div').attr('class', 'embryo-unprocessed')
                .text('Embryo reconstruction incomplete');
        }
    }

    function getMediaSelectionHandler(obj, media) {
        return function () {
            preventEventBubbling();
            var node = d3.select(this),
                parent = d3.select(this.parentNode),
                url = getMediaUrl(media, obj.context);
            parent.selectAll('.active').classed('active', false);
            node.classed('active', true);
            if (obj.specimenTitle)
                obj.specimenTitle.html(getMediaTitle(media));
            this.scrollIntoView(true);
            if (media.e === 'pdf')
                replacePdfIframe(obj.viewportContainer, url);
            dcc.mediaContextForQC = media;
        };
    }

    function getEmbryoSelectionHandler(obj, media) {
        return function () {
            preventEventBubbling();
            var node = d3.select(this),
                parent = d3.select(this.parentNode),
                url = getEmbryoMediaUrl(media, obj.context);
            parent.selectAll('.active').classed('active', false);
            node.classed('active', true);
            if (obj.specimenTitle)
                obj.specimenTitle.html(getMediaTitle(media));
            this.scrollIntoView(true);
            replaceEmbryoImage(media, obj.viewportContainer, url);
            dcc.mediaContextForQC = media;
        };
    }

    function isEmbryo(media) {
        return media.p === EMBRYO_PROCESSING_PHASE;
    }

    function getSpecimenSelectionHandler(obj, media, roi) {
        if (isEmbryo(media))
            return getEmbryoSelectionHandler(obj, media);
        else if (roi === undefined)
            return getMediaSelectionHandler(obj, media);
        else
            return getImageSelectionHandler(obj, media, roi);
    }

    /**
     * Encapsulates the region of interest selector.
     * 
     * @param {Object} thumbnail Region-of-interest container.
     * @param {Integer} ow Original image width before scaling.
     * @param {Integer} oh Original image height before scaling.
     * @param {Integer} tw Thumbnail image width.
     * @param {Object} viewport Associated viewport object.
     * @returns {Object} Region of interest object.
     */
    var RegionOfInterestSelector = function (thumbnail, ow, oh, tw, viewport) {
        this.thumbnail = thumbnail;
        this.ow = ow; /* original image width before scaling */
        this.oh = oh; /* original image height before scaling */
        this.ar = ow / oh; /* image aspect ratio */
        this.tw = tw; /* thumbnail width */
        this.viewport = viewport;
        this.init();
    };
    RegionOfInterestSelector.prototype = {
        init: function () {
            var me = this;
            me.roi = me.thumbnail.append('div')
                .attr('class', 'roi-selector')
                .attr('w', me.ow)
                .attr('h', me.oh)
                .classed('grab', true);
            me.events();
        },
        resize: function () {
            var me = this, viewport = me.viewport;
            me.scale = viewport.getScale() * 0.01; /* scaling of original */
            me.sw = me.ow * me.scale; /* scaled width of image */
            me.sh = me.oh * me.scale; /* scaled height of image */
            me.vw = viewport.width();
            me.vh = viewport.height();
            me.vr = me.vw / me.vh; /* viewport aspect ratio */
            me.th = me.tw / me.ar; /* height of thumbnail */
            me.wr = me.sw / me.vw; /* ratio of scaled image width to viewport width */
            me.rw = me.tw / me.wr; /* width of region-of-interest box */
            me.rh = me.rw / me.vr; /* height of region-of-interest box */

            /* check if original image is smaller than viewport */
            if (me.rh > me.th)
                me.rh = me.th;
            if (me.rw > me.tw)
                me.rw = me.tw;

            dom_width(me.roi, me.rw);
            dom_height(me.roi, me.rh);
        },
        events: function () {
            var me = this, roi = me.roi;
            roi.on('mousedown', function () {
                preventEventBubbling();
                if (!isDragging) {
                    isDragging = true;
                    d3.select('body').classed('unselectable', true);
                    roi.classed('grabbing', true).classed('grab', false);
                    var coord = d3.mouse(this.parentNode);
                    dragX = coord[0];
                    dragY = coord[1];
                }
            });
            roi.on('mousemove', function () {
                preventEventBubbling();
                if (isDragging) {
                    var coord = d3.mouse(this.parentNode),
                        left = dom_left(roi) - (dragX - coord[0]),
                        top = dom_top(roi) - (dragY - coord[1]),
                        leftTop = me.bound(left, top);
                    dom_left(roi, leftTop.l);
                    dom_top(roi, leftTop.t);
                    leftTop = me.roiToViewport(leftTop.l, leftTop.t);
                    me.viewport.move(leftTop.l, leftTop.t);
                    dragX = coord[0];
                    dragY = coord[1];
                }
            });
            roi.on('mouseup', function () {
                preventEventBubbling();
                if (isDragging) {
                    roi.classed('grabbing', false).classed('grab', true);
                    isDragging = false;
                }
            });
        },
        viewportToRoi: function (sl, st) {
            var me = this;
            return {
                'l': me.rw === me.tw ? 0 : me.tw * -sl / me.sw,
                't': me.rh === me.th ? 0 : me.th * -st / me.sh
            };
        },
        roiToViewport: function (rl, rt) {
            var me = this,
                /* ratio of roi top to thumbnail height */
                tr = rt / me.th,
                /* ratio of roi left to thumbnail width */
                lr = rl / me.tw;
            return {
                'l': -me.sw * lr,
                't': -me.sh * tr
            };
        },
        bound: function (left, top) {
            var me = this,
                ml = me.tw - me.rw, /* maximum left value for roi */
                mt = me.th - me.rh; /* maximum top value for roi */
            if (left < 0)
                left = 0;
            else if (left >= ml)
                left = ml;
            if (top < 0)
                top = 0;
            else if (top >= mt)
                top = mt;
            return {
                'l': left,
                't': top
            };
        },
        move: function (left, top) {
            var me = this, loc = me.viewportToRoi(left, top);
            dom_height(me.roi, me.rh);
            dom_width(me.roi, me.rw);
            dom_left(me.roi, loc.l);
            dom_top(me.roi, loc.t);
        }
    };
    function addRoiSelector(thumbnail, image, viewport) {
        var width = image.w, height = image.h,
            roiObj = new RegionOfInterestSelector(thumbnail,
                width, height, THUMBNAIL_WIDTH, viewport);
        return roiObj;
    }

    /**
     * Prepares the sex of the specimen for display.
     *
     * @param {String} sex Sex of the specimen from server.
     * @returns {String} Valid sex information.
     */
    function prepareSex(sex) {
        switch (sex) {
            case 0:
                sex = "Female";
                break;
            case 1:
                sex = "Male";
                break;
            default:
                sex = "Invalid";
        }
        return sex;
    }

    /**
     * Prepares the zygosity of the specimen for display.
     *
     * @param {Integer} zygosity Zygosity of the specimen from server.
     * @returns {String} Valid zygosity information.
     */
    function prepareZygosity(zygosity) {
        if (zygosity === undefined) {
            zygosity = "Invalid";
        } else {
            switch (zygosity) {
                case 0:
                    zygosity = "Heterozygous";
                    break;
                case 1:
                    zygosity = "Homozygous";
                    break;
                case 2:
                    zygosity = "Hemizygous";
                    break;
                default:
                    zygosity = "Invalid";
            }
        }
        return zygosity;
    }

    function getMediaDetails(media) {
        var c = "<table><tbody>";
        if (media.l)
            c += '<tr><td colspan="2" class="external-link"><a target="_blank" href="' +
                media.l + '">View full size on external viewer</a></td>';
        c += '<tr><td>Name:</td><td>' + media.an + '</td></tr>';
        c += '<tr><td>Sex:</td><td>' + prepareSex(media.g)
            + (media.gid === 0 ? ' (wildtype)' : ' (mutant)') + '</td></tr>';
        c += '<tr><td>Zygosity:</td><td>' + prepareZygosity(media.z) + '</td></tr>';
        c += '<tr><td>Assoc. param.:</td><td>' + (media.n === undefined ? 'unknown' : media.n) + '</td></tr>';
        c += '<tr><td>Assoc. key:</td><td>' + (media.k === undefined ? 'unknown' : media.k) + '</td></tr>';
        c += '<tr><td>Exp. date:</td><td>' + dateFormatter(new Date(media.d)) + '</td></tr>';
        return c + '</tbody></table>';
    }

    function getMediaTitle(media, shortTitle) {
        var c = "";
        if (media === undefined)
            return c;
        c += '<span>' + media.an + '</span>';
        if (!shortTitle) {
            c += '<span>' + prepareSex(media.g) + '</span>';
            c += '<span>' + prepareZygosity(media.z) + '</span>';
            c += '<span>' + dateFormatter(new Date(media.d)) + '</span>';
        }
        if (media.n === undefined || media.k === undefined) {
            c += '<span class="no-assoc-param">No associated parameter</span>';
        } else {
            c += '<span class="assoc-param">' + media.n + ' (' + media.k + ')</span>';
        }
        return c;
    }

    function addImageThumbnail(selector, thumbnail, media, obj) {
        var roiObj, img, viewport = obj.viewport,
            roiSelector = thumbnail.append('div')
            .attr('class', 'thumbnail-img');

        img = roiSelector.append('img')
            .attr('src-hold', getThumbnailUrl(media));
        if (isVisible(img.node(), selector))
            img.attr('src', img.attr('src-hold'));
        roiObj = addRoiSelector(roiSelector, media, viewport);
        thumbnail.node().onmouseup =
            getSpecimenSelectionHandler(obj, media, roiObj);
    }

    function addMediaThumbnail(thumbnail, media, obj) {
        thumbnail.node().onmouseup =
            getSpecimenSelectionHandler(obj, media);
        thumbnail.append('a')
            .attr('href', getMediaUrl(media, obj.context))
            .attr('target', '_blank')
            .append('div')
            .attr('class', 'thumbnail-' + media.e)
            .html(media.e + ' document');
    }

    function addEmbryoThumbnail(thumbnail, media, obj) {
        thumbnail.node().onmouseup =
            getSpecimenSelectionHandler(obj, media);
        thumbnail.append('a')
            .attr('href', getMediaUrl(media, obj.context))
            .attr('target', '_blank')
            .append('div')
            .attr('class', 'thumbnail-embryo')
            .html('Embryo reconstruction file');
    }

    function getMediaStatusMessage(status) {
        var msg = '';
        /* values must correspond to phenodcc_media.a_status */
        switch (status) {
            case 1:
                msg = 'is pending';
                break;
            case 2:
                msg = 'is running';
                break;
            case 3:
                msg = 'has finished';
                break;
            case 4:
                msg = 'was cancelled';
                break;
            case 5:
                msg = 'has failed';
                break;
        }
        return '<span class="media-status">' + msg + '</span>';
    }

    function getMediaPhaseMessage(phase) {
        var msg = '';
        /* values must correspond to phenodcc_media.phase */
        switch (phase) {
            case 1:
                msg = 'Media download ';
                break;
            case 2:
                msg = 'Checksum calculation ';
                break;
            case 3:
                msg = 'Tile generation ';
                break;
        }
        return '<span class="media-phase">' + msg + '</span>';
    }

    function getMediaProgress(media) {
        var msg = '';
        /* image media: requires three phases */
        if (media.i) {
            if (media.p < 3 && media.s === 3) {
                /* if not all phases are done, show next phase pending */
                msg = getMediaPhaseMessage(media.p + 1);
                msg += getMediaStatusMessage(1);
            } else {
                /* otherwise. show the current phase and status */
                msg = getMediaPhaseMessage(media.p);
                msg += getMediaStatusMessage(media.s);
            }
        } else {
            if (media.p < 2 && media.s === 3) {
                msg = getMediaPhaseMessage(media.p + 1);
                msg += getMediaStatusMessage(1);
            } else {
                msg = getMediaPhaseMessage(media.p);
                msg += getMediaStatusMessage(media.s);
            }
        }
        return msg;
    }

    function showMediaProgress(thumbnail, media) {
        thumbnail.append('div')
            .attr('class', 'media-progress')
            .classed('phase-failed', media.s === 5)
            .html(getMediaProgress(media));
    }

    function addThumbnail(obj, media, index) {
        var showProgress = true, selector = obj.specimenSelector,
            selectorDom = selector.node(),
            thumbnail = selector.append('div')
            .attr('class', 'thumbnail')
            .attr('mid', media.mid)
            .attr('aid', media.aid);

        thumbnail.append('div')
            .attr('class', 'animal-media')
            .html(getMediaDetails(media));

        obj.regionOfInterest = undefined;
        thumbnail.node().thumbnailIndex = index;

        if (media.i) { /* media is image */
            /* if image tiles were generated successfully */
            if (media.p === 3 && media.s === 3) {
                addImageThumbnail(selectorDom, thumbnail, media, obj);
                showProgress = false;
            }
        } else {
            /* is this embryo reconstruction? */
            if (isEmbryo(media)) {
                addEmbryoThumbnail(thumbnail, media, obj);
                showProgress = false;
            } else if (media.p === 2 && media.s === 3) {
                /* if media downloaded successfully and checksum was calculated */
                addMediaThumbnail(thumbnail, media, obj);
                showProgress = false;
            }
        }

        if (showProgress)
            showMediaProgress(thumbnail, media);
    }

    function downloadMediaDetails(obj, successHandler, failureHandler, container) {
        if (container)
            container.classed(STR_LOADING, true);
        d3.json(IMAGE_VIEWER_HOST + 'rest/mediafiles/'
            + obj.context.contextPath, function (data) {
                if (container)
                    container.classed(STR_LOADING, false);
                if (data.success) {
                    if (successHandler)
                        successHandler(data.details);
                } else {
                    if (failureHandler)
                        failureHandler();
                }
            });
    }

    function getAndFillSpecimen(obj, includeType) {
        downloadMediaDetails(obj,
            function (data) {
                obj.data = data;
                if (fillSpecimen(obj, includeType) !== undefined)
                    obj.updateNotification(STR_NO_IMAGES, false);
            },
            function () {
                delete obj.data;
            }, obj.specimenSelector);
    }

    function fillSpecimen(obj, includeType) {
        var data = obj.data, i, j, c = data.length, datum, firstSpecimen,
            countWT = 0, countM = 0, doInclude, numThumbnailsToInclude = 0,
            pageSize = obj.thumbnailPager.pageSize,
            start = obj.thumbnailPager.currentPage * pageSize,
            end = start + pageSize;
        clear(obj.specimenSelector);
        doInclude = obj.doInclude = function (datum) {
            var matchParameterKey = obj.parent.filter, select = true;
            if ((includeType & INCLUDE_ONLY_WILDTYPE) && datum.gid !== 0)
                select = false;
            else if ((includeType & INCLUDE_ONLY_MUTANT) && datum.gid === 0)
                select = false;
            return select && (matchParameterKey === undefined
                || datum.k === matchParameterKey);
        };

        if (includeType & INCLUDE_BOTH) {
            for (i = 0; i < c; ++i) {
                datum = data[i];
                if (doInclude(datum)) {
                    if (++numThumbnailsToInclude <= start)
                        continue;
                    if (firstSpecimen === undefined)
                        firstSpecimen = datum;
                    addThumbnail(obj, datum, i);
                    if (datum.gid !== 0)
                        ++countM;
                    else
                        ++countWT;
                    if (numThumbnailsToInclude === end)
                        break;
                }
            }
        } else if (includeType & INCLUDE_ONLY_WILDTYPE) {
            for (i = 0, j = 0; i < c; ++i) {
                datum = data[i];
                if (doInclude(datum)) {
                    if (datum.gid === 0) {
                        if (++numThumbnailsToInclude <= start)
                            continue;
                        if (firstSpecimen === undefined)
                            firstSpecimen = datum;
                        addThumbnail(obj, datum, j++);
                        if (datum.gid !== 0)
                            ++countM;
                        else
                            ++countWT;
                        if (numThumbnailsToInclude === end)
                            break;
                    }
                }
            }
            obj.selectSpecimen(data[0].aid, data[0].mid);
        } else if (includeType & INCLUDE_ONLY_MUTANT) {
            for (i = 0, j = 0; i < c; ++i) {
                datum = data[i];
                if (doInclude(datum)) {
                    if (datum.gid !== 0) {
                        if (++numThumbnailsToInclude <= start)
                            continue;
                        if (firstSpecimen === undefined)
                            firstSpecimen = datum;
                        addThumbnail(obj, datum, j++);
                        if (datum.gid !== 0)
                            ++countM;
                        else
                            ++countWT;
                        if (numThumbnailsToInclude === end)
                            break;
                    }
                }
            }
        }
        if ((countWT + countM) > 0 && obj.specimenToSelect) {
            obj.updateNotification(STR_NO_IMAGES, false);
            if (obj.selectSpecimen(obj.specimenToSelect.aid,
                obj.specimenToSelect.mid))
                firstSpecimen = false;
        }
        if (firstSpecimen) {
            obj.updateNotification(STR_NO_IMAGES, false);
            obj.selectSpecimen(firstSpecimen.aid, firstSpecimen.mid);
        }
        obj.thumbnailPager.render(includeType);
    }

    function createViewerInterface(obj) {
        var container = obj.container,
            selectorOrientation = obj.selectorOrientation;
        switch (selectorOrientation) {
            case STR_LEFT:
                obj.viewportContainer = container.append('div')
                    .attr('class', STR_VIEWPORT_CONTAINER + STR_RIGHT);
                obj.specimenSelector = container.append('div')
                    .attr('class', STR_SPECIMEN_SELECTOR + STR_LEFT);
                break;
            case STR_RIGHT:
                obj.viewportContainer = container.append('div')
                    .attr('class', STR_VIEWPORT_CONTAINER + STR_LEFT);
                obj.specimenSelector = container.append('div')
                    .attr('class', STR_SPECIMEN_SELECTOR + STR_RIGHT);
                break;
            case STR_TOP:
                obj.viewportContainer = container.append('div')
                    .attr('class', STR_VIEWPORT_CONTAINER + STR_BOTTOM);
                obj.specimenSelector = container.append('div')
                    .attr('class', STR_SPECIMEN_SELECTOR + STR_TOP);
                break;
            case STR_BOTTOM: /* by default place on bottom */
            default:
                obj.viewportContainer = container.append('div')
                    .attr('class', STR_VIEWPORT_CONTAINER + STR_TOP);
                obj.specimenSelector = container.append('div')
                    .attr('class', STR_SPECIMEN_SELECTOR + STR_BOTTOM);
        }
        obj.thumbnailPagerContainer = container.append('div')
            .attr('class', 'list-pager-container unselectable');
        obj.viewport = new Viewport(obj);
        obj.viewControl = new ViewControl(obj);
        obj.titleBar = obj.viewportContainer
            .append('div').attr('class', STR_IMAGE_PANEL + 'title-bar');
        obj.download = obj.titleBar.append('a')
            .attr('target', '_blank')
            .attr('class', STR_IMAGE_PANEL + 'download')
            .attr('title', 'Download original media file');
        obj.external = obj.titleBar.append('a')
            .attr('target', '_blank')
            .attr('class', STR_IMAGE_PANEL + 'external')
            .attr('title', 'Visit external viewer')
            .style('display', 'none');

        if (obj.title)
            obj.titleBar.append('div')
                .attr('class', STR_IMAGE_PANEL + 'specimen-type')
                .text(obj.title);

        obj.specimenTitle = obj.titleBar.append('div')
            .attr('class', STR_IMAGE_PANEL + 'specimen-title');


        obj.specimenSelector.node().onscroll = function () {
            var node = d3.select(this), container = this;
            node.selectAll('img')
                .each(function () {
                    var img = d3.select(this);
                    if (img.attr('src') === null && isVisible(this, container))
                        img.attr('src', img.attr('src-hold'));
                });
        };
        obj.thumbnailPager = new ThumbnailPager(obj);
    }

    function refitViewerInterface(obj) {
        var viewportContainer = obj.viewportContainer,
            specimenSelector = obj.specimenSelector,
            /* we subtract 1 pixel for the panel separator */
            temp = obj.splitType === undefined ? 0 : 1;

        switch (obj.selectorOrientation) {
            case STR_LEFT:
            case STR_RIGHT:
                temp = dom_height(obj.container) - temp;
                dom_height(viewportContainer, temp);
                dom_height(specimenSelector, temp - dom_height(obj.thumbnailPagerContainer));
                dom_width(specimenSelector, SPECIMEN_SELECTOR_WIDTH);
                dom_width(obj.thumbnailPagerContainer, SPECIMEN_SELECTOR_WIDTH);
                dom_width(viewportContainer,
                    dom_width(obj.container) - dom_width(obj.specimenSelector));
                break;
            case STR_TOP:
            case STR_BOTTOM:
            default:
                temp = dom_width(obj.container) - temp;
                dom_width(viewportContainer, temp);
                dom_width(specimenSelector, temp);
                dom_width(obj.thumbnailPagerContainer, temp);
                dom_height(specimenSelector, SPECIMEN_SELECTOR_HEIGHT);
                dom_height(viewportContainer,
                    dom_height(obj.container)
                    - dom_height(obj.specimenSelector)
                    - dom_height(obj.thumbnailPagerContainer));
        }
        obj.viewControl.refit();
        obj.specimenSelector.node().onscroll();
        if (obj.regionOfInterest)
            obj.regionOfInterest.resize();
        obj.viewport.refit();
        obj.thumbnailPager.refit();
    }

    dcc.ImageViewer = function (container, selectorOrientation, obj) {
        this.parent = obj;
        this.container = container;
        this.id = container.id;
        this.title = container.title;
        this.selectorOrientation = selectorOrientation;
        this.splitType = container.splitType;

        this.imageProcessingConfig = {
            invert: false,
            brightness: 0,
            contrast: 1,
            red: true,
            blue: true,
            green: true
        };

        this.scales = [10, 25, 50, 75, 100];
        this.init();
    };

    dcc.ImageViewer.prototype = {
        init: function () {
            var me = this;
            createViewerInterface(me);
            refitViewerInterface(me);
        },
        refit: function () {
            var me = this;
            me.specimenTitle.html(smallScreen ? me.mediaShortTitle : me.mediaTitle);
            refitViewerInterface(me);
        },
        update: function (context, includeType, data) {
            var me = this;
            me.context = context;
            me.updateNotification(STR_NO_IMAGES, true);
            if (data === undefined) { /* viewer is self contained */
                if (me.data === undefined)
                    getAndFillSpecimen(me, includeType);
                else
                    fillSpecimen(me, includeType);
            } else { /* viewer uses data supplied by external container */
                if (data instanceof Array) {
                    me.data = data;
                    fillSpecimen(me, includeType);
                } else
                    getAndFillSpecimen(me, includeType);
            }
        },
        selectSpecimen: function (aid, mid) {
            var me = this, foundSpecimen = false,
                key = '.thumbnail[aid="' + aid + '"]',
                selection;
            me.specimenToSelect = {
                'aid': aid,
                'mid': mid
            };
            if (mid !== undefined)
                key += '[mid="' + mid + '"]';
            selection = me.specimenSelector.select(key);
            if (!selection.empty()) {
                selection = selection.node();
                if (selection && selection.onmouseup) {
                    foundSpecimen = true;
                    selection.onmouseup();
                }
            }
            return foundSpecimen;
        },
        updateNotification: function (cls, show) {
            var me = this;
            me.specimenSelector.classed(cls, show);
        },
        setControl: function (config) {
            var me = this;
            me.viewControl.setControl(config);
        },
        getControl: function () {
            var me = this;
            return me.viewControl.getControl();
        }
    };

    function addImageViewerPanel(obj, id, cls, orientation, title, splitType) {
        var container = obj.content, panel = container.append('div')
            .attr('id', id)
            .attr('class', cls);
        panel.parent = obj;
        panel.title = title;
        panel.id = id;
        panel.splitType = splitType;
        panel.viewer = new dcc.ImageViewer(panel, orientation, obj);
        return panel;
    }

    function ViewerToolbar(obj) {
        this.parent = obj;
        this.init();
    }

    ViewerToolbar.prototype = {
        init: function () {
            var me = this, parent = me.parent,
                container = parent.container,
                toolbar = parent.externalToolbar;

            if (toolbar === undefined)
                toolbar = container.append('div')
                    .attr('class', 'image-viewer-toolbar');
            else
                toolbar.selectAll('*').remove();

            if (parent.exitHandler !== undefined) {
                toolbar.append('div')
                    .attr('class', 'exit-image-viewer')
                    .text('Exit viewer')
                    .attr('title', 'Click to exit image viewer')
                    .on('click', parent.exitHandler);
            }

            detectSmallScreenSize(container);
            toolbar.append('div')
                .attr('class', 'image-viewer-title')
                .html(smallScreen ? parent.shortTitle : parent.title);

            var notEmbryoParameter = true,
                embryoParameters = {
                    "IMPC_EOL_001_001": true,
                    "IMPC_EMO_001_001": true,
                    "IMPC_EMA_001_001": true
                };

            if (embryoParameters[me.parent.context.qeid])
                notEmbryoParameter = false;


            if (notEmbryoParameter)
                toolbar.append('div')
                    .attr('class', 'viewer-controls')
                    .attr('title', 'Click to show/hide image processing controls')
                    .classed(STR_CONTROL_IS_ON, true)
                    .on('click', function () {
                        var node = d3.select(this);
                        if (node.classed(STR_CONTROL_IS_ON)) {
                            node.classed(STR_CONTROL_IS_ON, false);
                            parent.viewControls(false);
                        } else {
                            node.classed(STR_CONTROL_IS_ON, true);
                            parent.viewControls(true);
                        }
                    });
            toolbar.append('div')
                .attr('class', 'specimen-selector')
                .attr('title', 'Click to show/hide specimen selector')
                .classed(STR_CONTROL_IS_ON, true)
                .on('click', function () {
                    var node = d3.select(this);
                    if (node.classed(STR_CONTROL_IS_ON)) {
                        node.classed(STR_CONTROL_IS_ON, false);
                        parent.specimenSelectors(false);
                    } else {
                        node.classed(STR_CONTROL_IS_ON, true);
                        parent.specimenSelectors(true);
                    }
                });

            toolbar.append('div')
                .attr('class', 'mode-switcher')
                .attr('title', 'Click to switch between single and comparative modes')
                .classed('single', parent.splitType === undefined)
                .on('click', function () {
                    var node = d3.select(this);
                    if (node.classed('single')) {
                        node.classed('single', false);
                        parent.toggleMode('comparative');
                    } else {
                        node.classed('single', true);
                        parent.toggleMode('single');
                    }
                });

            if (parent.splitType !== undefined) {
                toolbar.append('div')
                    .attr('class', 'switch-split-type')
                    .attr('title', 'Click to switch between vertical/horizontal splitting')
                    .classed('vertical', function () {
                        return parent.splitType === 'horizontal';
                    })
                    .classed('horizontal', function () {
                        return parent.splitType === 'vertical';
                    })
                    .on('click', function () {
                        var node = d3.select(this);
                        if (node.classed('vertical')) {
                            node.classed('vertical', false);
                            node.classed('horizontal', true);
                            parent.splitType = 'vertical';
                            parent.split(true);
                        } else {
                            node.classed('horizontal', false);
                            node.classed('vertical', true);
                            parent.splitType = 'horizontal';
                            parent.split(false);
                        }
                    });

                if (notEmbryoParameter)
                    toolbar.append('div')
                        .attr('class', 'sync-comparative')
                        .attr('title', 'Click to sync controls between comparative images')
                        .classed(STR_CONTROL_IS_ON, syncControls)
                        .on('click', function () {
                            var node = d3.select(this);
                            if (node.classed(STR_CONTROL_IS_ON)) {
                                node.classed(STR_CONTROL_IS_ON, false);
                                syncControls = false;
                            } else {
                                node.classed(STR_CONTROL_IS_ON, true);
                                syncControls = true;
                            }
                        });
            }
            me.node = toolbar;
        }
    };

    dcc.ComparativeImageViewer = function (id, config) {
        this.id = id;
        if (config) {
            this.title = config.title;
            this.shortTitle = config.shortTitle;
            this.splitType = config.splitType;
            this.container = d3.select('#' + id);
            this.exitHandler = config.exitHandler;
            this.externalToolbar = config.toolbar;
            this.filter = config.filter;
            if (config.host !== undefined)
                IMAGE_VIEWER_HOST = config.host;
        }
        clear(this.container);
    };

    function detectSmallScreenSize(container) {
        smallScreen = dom_width(container) < SMALL_SCREEN_WIDTH;
    }

    dcc.ComparativeImageViewer.prototype = {
        clear: function () {
            var me = this;
            clear(me.container);
        },
        fail: function (type, title, message) {
            var me = this, node;
            clear(me.container);
            node = me.container.append('div').attr('class', type + '-message');
            node.append('div').html(title);
            node.append('div').html(message);
        },
        render: function () {
            var me = this, container = me.container, id = '-' + me.id;
            clear(me.container);
            me.toolbar = new ViewerToolbar(me);
            me.content = container.append('div').attr('class', 'viewer-panels');
            dom_height(me.content, dom_height(container) - dom_height(me.toolbar.node));

            switch (me.splitType) {
                case 'vertical':
                    me.wildtypePanel = addImageViewerPanel(me,
                        STR_IMAGE_PANEL + STR_WILDTYPE + id,
                        STR_IMAGE_PANEL + STR_LEFT,
                        STR_BOTTOM, STR_WILDTYPE, me.splitType);
                    me.mutantPanel = addImageViewerPanel(me,
                        STR_IMAGE_PANEL + STR_MUTANT + id,
                        STR_IMAGE_PANEL + STR_RIGHT,
                        STR_BOTTOM, STR_MUTANT, me.splitType);
                    break;
                case 'horizontal':
                    me.wildtypePanel = addImageViewerPanel(me,
                        STR_IMAGE_PANEL + STR_WILDTYPE + id,
                        STR_IMAGE_PANEL + STR_TOP,
                        STR_LEFT, STR_WILDTYPE, me.splitType);
                    me.mutantPanel = addImageViewerPanel(me,
                        STR_IMAGE_PANEL + STR_MUTANT + id,
                        STR_IMAGE_PANEL + STR_BOTTOM,
                        STR_LEFT, STR_MUTANT, me.splitType);
                    break;
                default:
                    me.panel = addImageViewerPanel(me,
                        STR_IMAGE_PANEL + STR_WILDTYPE + id,
                        STR_IMAGE_PANEL + 'single',
                        STR_LEFT);
            }
            d3.select(window).on('resize', function () {
                detectSmallScreenSize(me.container);
                me.toolbar.node.select('.image-viewer-title')
                    .html(smallScreen ? me.shortTitle : me.title);
                me.refit();
            });
        },
        view: function (cid, gid, sid, qeid, pid, lid) {
            var me = this, MESSAGE =
                'The image viewer requires four parameters that identifies ' +
                'the centre, genotype, strain and parameter. Optionally, it ' +
                'also accepts a pipeline identifier and procedure identifier.' +
                ' If the pipeline or procedure is unspecified, images from ' +
                'all pipelines and procedures associated with the supplied ' +
                'parameter are shown.';
            if (cid === undefined || cid === null)
                me.fail(STR_ERROR, 'Invalid centre identifier', MESSAGE);
            else if (gid === undefined || gid === null)
                me.fail(STR_ERROR, 'Invalid genotype identifier', MESSAGE);
            else if (sid === undefined || sid === null)
                me.fail(STR_ERROR, 'Invalid strain identifier', MESSAGE);
            else if (qeid === undefined || qeid === null)
                me.fail(STR_ERROR, 'Invalid parameter key', MESSAGE);
            else {
                me.context = {
                    cid: cid,
                    gid: gid,
                    sid: sid,
                    qeid: qeid,
                    pid: pid, /* optional */
                    lid: lid /* optional */
                };
                me.context.contextPath = getQueryParam(me.context, true);
                me.render();
                me.activateContext();
            }
        },
        applyContext: function () {
            var me = this;
            if (me.splitType === undefined)
                me.panel.viewer.update(me.context, INCLUDE_BOTH, me.data);
            else {
                me.update(STR_WILDTYPE, INCLUDE_ONLY_WILDTYPE, me.data);
                me.update(STR_MUTANT, INCLUDE_ONLY_MUTANT, me.data);
            }
        },
        updateNotification: function (cls, show) {
            var me = this;
            if (me.panel) {
                if (me.panel.viewer)
                    me.panel.viewer.updateNotification(cls, show);
            } else {
                if (me.mutantPanel)
                    me.mutantPanel.viewer.updateNotification(cls, show);
                if (me.wildtypePanel)
                    me.wildtypePanel.viewer.updateNotification(cls, show);
            }
        },
        activateContext: function (forcedUpdate) {
            var me = this, container = null;
            if (forcedUpdate || !me.data) {
                me.updateNotification(STR_NO_IMAGES, false);
                me.updateNotification(STR_LOADING, true);
                downloadMediaDetails(me,
                    function (data) {
                        me.data = data;
                        me.applyContext();
                        me.updateNotification(STR_LOADING, false);
                    },
                    function () {
                        delete me.data;
                        me.updateNotification(STR_LOADING, false);
                        me.updateNotification(STR_NO_IMAGES, true);
                    }, container);
            } else
                me.applyContext();
        },
        update: function (which, includeType, data) {
            var me = this, panel;
            switch (which) {
                case STR_WILDTYPE: /* first panel */
                    panel = me.wildtypePanel;
                    break;
                case STR_MUTANT: /*second panel */
                    panel = me.mutantPanel;
                    break;
            }
            if (panel)
                panel.viewer.update(me.context, includeType, data);
        },
        refit: function () {
            var me = this;
            dom_height(me.content, dom_height(me.container) - dom_height(me.toolbar.node));
            if (me.splitType === undefined)
                me.panel.viewer.refit();
            else {
                me.wildtypePanel.viewer.refit();
                me.mutantPanel.viewer.refit();
            }
        },
        split: function (vertically) {
            var me = this, container = me.container;
            if (me.splitType === undefined)
                return;

            if (vertically) {
                container.select(STR_IMAGE_PANEL_CLASS + STR_TOP)
                    .attr('class', STR_IMAGE_PANEL + STR_LEFT);
                container.select(STR_IMAGE_PANEL_CLASS + STR_BOTTOM)
                    .attr('class', STR_IMAGE_PANEL + STR_RIGHT);

                container.selectAll(STR_SPECIMEN_SELECTOR_CLASS + STR_LEFT)
                    .classed(STR_SPECIMEN_SELECTOR + STR_LEFT, false)
                    .classed(STR_SPECIMEN_SELECTOR + STR_BOTTOM, true);
                container.selectAll(STR_VIEWPORT_CONTAINER_CLASS + STR_RIGHT)
                    .attr('class', STR_VIEWPORT_CONTAINER + STR_TOP);
                me.wildtypePanel.viewer.selectorOrientation = STR_BOTTOM;
                me.mutantPanel.viewer.selectorOrientation = STR_BOTTOM;
            } else {
                container.select(STR_IMAGE_PANEL_CLASS + STR_LEFT)
                    .attr('class', STR_IMAGE_PANEL + STR_TOP);
                container.select(STR_IMAGE_PANEL_CLASS + STR_RIGHT)
                    .attr('class', STR_IMAGE_PANEL + STR_BOTTOM);
                container.selectAll(STR_SPECIMEN_SELECTOR_CLASS + STR_BOTTOM)
                    .classed(STR_SPECIMEN_SELECTOR + STR_BOTTOM, false)
                    .classed(STR_SPECIMEN_SELECTOR + STR_LEFT, true);
                container.selectAll(STR_VIEWPORT_CONTAINER_CLASS + STR_TOP)
                    .attr('class', STR_VIEWPORT_CONTAINER + STR_RIGHT);
                me.wildtypePanel.viewer.selectorOrientation = STR_LEFT;
                me.mutantPanel.viewer.selectorOrientation = STR_LEFT;
            }
            me.refit();
        },
        selectSpecimen: function (aid, mid) {
            var me = this;
            if (me.panel) /* single panel for combined */
                me.panel.viewer.selectSpecimen(aid, mid);
            else { /* split into two panels */
                me.wildtypePanel.viewer.selectSpecimen(aid, mid);
                me.mutantPanel.viewer.selectSpecimen(aid, mid);
            }
        },
        specimenSelectors: function (doShow) {
            var me = this;
            me.container.selectAll('[class*="specimen-selector-"]')
                .style('display', doShow ? 'block' : 'none');
            me.container.selectAll('.list-pager-container')
                .style('display', doShow ? 'block' : 'none');
            me.refit();
        },
        viewControls: function (doShow) {
            var me = this;
            me.container.selectAll('.view-control')
                .style('display', doShow ? 'block' : 'none');
        },
        setControl: function (config) {
            var me = this;
            if (me.panel)
                me.panel.viewer.setControl(config);
            else {
                me.wildtypePanel.viewer.setControl(config);
                me.mutantPanel.viewer.setControl(config);
            }
        },
        toggleMode: function (mode) {
            var me = this;
            me.splitType = mode === 'single' ? undefined : 'vertical';
            delete me.panel;
            delete me.wildtypePanel;
            delete me.mutantPanel;
            me.render();
            me.activateContext();
        }
    };
})();