/*
 * Tencent is pleased to support the open source community by making
 * 蓝鲸智云-权限中心(BlueKing-IAM) available.
 *
 * Copyright (C) 2021 THL A29 Limited, a Tencent company.  All rights reserved.
 *
 * 蓝鲸智云-权限中心(BlueKing-IAM) is licensed under the MIT License.
 *
 * License for 蓝鲸智云-权限中心(BlueKing-IAM):
 *
 * ---------------------------------------------------
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
 * documentation files (the "Software"), to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
 * to permit persons to whom the Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all copies or substantial portions of
 * the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
 * THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
 * CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
*/

const nodeList = [];
const clickCtx = '$clickoutSideCtx';
let beginClick;
let seed = 0;

document.addEventListener('mousedown', event => (beginClick = event));

document.addEventListener('mouseup', event => {
  nodeList.forEach(node => {
    node[clickCtx].clickoutSideHandler(event, beginClick);
  });
});

const clickoutSide = {
  bind (el, binding, vNode) {
    nodeList.push(el);
    const id = seed++;
    const clickoutSideHandler = (mouseup = {}, mousedown = {}) => {
      if (!vNode.context // 点击在 vue 实例之外的 DOM 上
        || !mouseup.target
        || !mousedown.target
        || el.contains(mouseup.target) // 鼠标按下时的 DOM 节点是当前展开的组件的子元素
        || el.contains(mousedown.target) // 鼠标松开时的 DOM 节点是当前展开的组件的子元素
        || el === mouseup.target // 鼠标松开时的 DOM 节点是当前展开的组件的根元素
        || (vNode.context.popup // 当前点击元素是有弹出层的
            && (
              vNode.context.popup.contains(mouseup.target) // 鼠标按下时的 DOM 节点是当前有弹出层元素的子节点
                || vNode.context.popup.contains(mousedown.target) // 鼠标松开时的 DOM 节点是当前有弹出层元素的子节点
            )
        )
      ) {
        return;
      }

      if (binding.expression // 传入了指令绑定的表达式
        && el[clickCtx].callbackName // 当前元素的 clickOutside 对象中有回调函数名
        && vNode.context[el[clickCtx].callbackName] // vNode 中存在回调函数
      ) {
        vNode.context[el[clickCtx].callbackName](mouseup, mousedown, el);
      } else {
        el[clickCtx].bindingFn && el[clickCtx].bindingFn(mouseup, mousedown, el);
      }
    };
    el[clickCtx] = {
      id,
      clickoutSideHandler,
      callbackName: binding.expression,
      callbackFn: binding.value
    };
  },
  update (el, binding) {
    const { expression, value } = binding;
    el[clickCtx] = { ...el[clickCtx], ...{ callbackName: expression, callbackFn: value } };
  },
  unbind (el) {
    for (let i = 0, len = nodeList.length; i < len; i++) {
      if (nodeList[i][clickCtx].id === el[clickCtx].id) {
        nodeList.splice(i, 1);
        break;
      }
    }
  }
};

export default clickoutSide;
