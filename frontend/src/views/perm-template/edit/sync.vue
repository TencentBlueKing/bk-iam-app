<template>
  <div class="iam-template-sync-wrapper" v-bkloading="{ isLoading: syncLoading, opacity: 1 }">
    <!-- eslint-disable max-len -->
    <bk-table
      v-if="!syncLoading"
      :data="tableList"
      col-border
      border
      size="small"
      ext-cls="iam-template-sync-table-cls"
      :cell-class-name="getCellClass"
      @cell-mouse-enter="handleCellMouseEnter"
      @cell-mouse-leave="handleCellMouseLeave">
      <bk-table-column
        :label="$t(`m.permTemplateDetail['关联的用户组']`)"
        :resizable="false"
        :width="180"
        fixed="left"
        prop="name">
      </bk-table-column>
      <template v-for="(item, index) in addProps">
        <bk-table-column
          :key="index"
          :min-width="200"
          :resizable="false"
          :prop="item.id"
          :render-header="renderAddActionHeader"
          :label="item.label">
          <template slot-scope="{ row, $index }">
            <div class="relation-content-wrapper">
              <template v-if="!row.add_actions[index].isEmpty">
                <div v-for="(_, groIndex) in row.add_actions[index].resource_groups" :key="_.id">
                  <div class="relation-content-item"
                    v-for="(content, contentIndex) in _.related_resource_types"
                    :key="`${index}${contentIndex}`">
                    <div class="content-name">{{ content.name }}</div>
                    <div class="content">
                      <render-condition
                        :ref="`condition_${index}_${$index}_${contentIndex}_ref`"
                        :value="content.value"
                        :params="curCopyParams"
                        :is-empty="content.empty"
                        :can-view="row.canView"
                        :can-paste="content.canPaste"
                        :is-error="content.isError"
                        @on-mouseover="handlerConditionMouseover(content, row)"
                        @on-mouseleave="handlerConditionMouseleave(content)"
                        @on-restore="handlerOnRestore(content)"
                        @on-copy="handlerOnCopy(content, $index, contentIndex, index, row.add_actions[index])"
                        @on-paste="handlerOnPaste(...arguments, content)"
                        @on-batch-paste="handlerOnBatchPaste(...arguments, content, $index, contentIndex, index)"
                        @on-click="showResourceInstance(row, content, contentIndex, $index, index, groIndex)" />
                    </div>
                  </div>
                </div>
                <bk-popover
                  :ref="`popover_${index}_${$index}_ref`"
                  trigger="click"
                  class="iam-template-sync-popover-cls"
                  theme="light"
                  placement="right"
                  :on-hide="() => handleHidePopover(row.add_actions[index])"
                  :on-show="() => handleShowPopover(row.add_actions[index])">
                  <div class="edit-wrapper" v-if="!!row.add_actions[index].showAction">
                    <spin-loading v-if="row.add_actions[index].loading" />
                    <Icon type="edit-fill" v-else />
                  </div>
                  <div slot="content" class="sync-popover-content">
                    <p class="refer-title" v-if="isShowBatchRefer(row.add_actions[index])">
                      <Icon type="down-angle" />{{ $t(`m.permTemplateDetail['批量引用已有的操作实例']`) }}
                    </p>
                    <template v-if="batchReferAction(row.add_actions[index]).length > 0">
                      <p v-for="resItem in batchReferAction(row.add_actions[index])"
                        :key="resItem.id"
                        class="cursor"
                        @click.stop="handleReferInstance(resItem, row.add_actions[index], row, index, $index)">
                        {{ resItem.name }}
                      </p>
                    </template>
                    <template v-if="!isShowBatchRefer(row.add_actions[index]) && batchReferAction(row.add_actions[index]).length === 0">
                      {{ $t(`m.common['暂无数据']`) }}
                    </template>
                  </div>
                </bk-popover>
              </template>
              <template v-else>
                {{ $t(`m.common['无需关联实例']`) }}
              </template>
            </div>
          </template>
        </bk-table-column>
      </template>
      <template v-for="(item, index) in deleteProps">
        <bk-table-column
          :key="item.id"
          :min-width="200"
          :resizable="false"
          :render-header="renderDeleteActionHeader"
          :label="item.label">
          <template slot-scope="{ row }">
            <div class="relation-content-wrapper">
              <template v-if="!row.delete_actions[index].isEmpty">
                <div v-for="(_, groIndex) in row.delete_actions[index].resource_groups" :key="_.id">
                  <p class="related-resource-item"
                    v-for="subItem in _.related_resource_types"
                    :key="subItem.type"
                    @click.stop="handleViewResource(row, index, groIndex)">
                    <render-resource-popover
                      :key="subItem.type"
                      :data="subItem.condition"
                      :value="`${subItem.name}：${subItem.value}`"
                      :max-width="185"
                      @on-view="handleViewResource(row, index, groIndex)" />
                  </p>
                </div>
              </template>
              <template v-else>
                {{ $t(`m.common['无需关联实例']`) }}
              </template>
            </div>
          </template>
        </bk-table-column>
      </template>
    </bk-table>
    <div class="pagination-wrapper" v-if="pagination.totalPage > 1 && !syncLoading">
      <div class="page-display">
        {{ pagination.current }} / {{ pagination.totalPage }}
      </div>
      <bk-button
        theme="primary"
        :loading="prevLoading"
        :disabled="pagination.current < 2"
        style="margin-left: 5px;"
        @click="handlePrevPage">
        {{ $t(`m.common['上一页']`) }}
      </bk-button>
      <bk-button
        v-if="!isLastPage"
        theme="primary"
        :loading="nextLoading"
        style="margin-left: 6px;"
        @click="handleNextPage">
        {{ isAddActionEmpty ? $t(`m.common['下一页']`) : $t(`m.common['确认']`) }}
      </bk-button>
    </div>

    <bk-sideslider
      :is-show.sync="isShowSideslider"
      :title="sidesliderTitle"
      :width="640"
      :quick-close="true"
      @animation-end="handleAnimationEnd">
      <div slot="content">
        <render-detail :data="previewData" />
      </div>
    </bk-sideslider>

    <bk-sideslider
      :is-show="isShowInstanceSideslider"
      :title="instanceSidesliderTitle"
      :width="resourceSliderWidth"
      quick-close
      transfer
      ext-cls="relate-instance-sideslider"
      @update:isShow="handleResourceCancel('mask')">
      <div slot="content" class="sideslider-content">
        <render-resource
          ref="renderResourceRef"
          :key="`${curIndex}${curResIndex}${curActionIndex}`"
          :data="condition"
          :original-data="originalCondition"
          :flag="curFlag"
          :selection-mode="curSelectionMode"
          :disabled="curDisabled"
          :params="params"
          :res-index="curResIndex"
          :cur-scope-action="curScopeAction"
          @on-init="handleOnInit" />
      </div>
      <div slot="footer" style="margin-left: 25px;">
        <bk-button theme="primary" :disabled="disabled" @click="handleResourceSubmit">{{ $t(`m.common['保存']`) }}</bk-button>
        <bk-button style="margin-left: 10px;" :disabled="disabled" @click="handleResourceCancel('cancel')">{{ $t(`m.common['取消']`) }}</bk-button>
      </div>
    </bk-sideslider>
  </div>
</template>
<script>
  import _ from 'lodash';
  import { mapGetters } from 'vuex';
  import SyncPolicy from '@/model/template-sync-policy';
  import Condition from '@/model/condition';
  import { leaveConfirm } from '@/common/leave-confirm';
  import RenderResourcePopover from '@/components/iam-view-resource-popover';
  import RenderCondition from '../components/render-condition';
  import RenderDetail from '../components/render-detail';
  import RenderResource from '../components/render-resource';
  export default {
    name: '',
    provide: function () {
      return {
        getResourceSliderWidth: () => this.resourceSliderWidth
      };
    },
    components: {
      RenderResourcePopover,
      RenderCondition,
      RenderDetail,
      RenderResource
    },
    props: {
      id: {
        type: [String, Number],
        default: ''
      },
      cloneAction: {
        type: Array,
        default: () => []
      },
      addAction: {
        type: Array,
        default: () => []
      }
    },
    data () {
      return {
        pagination: {
          current: 1,
          limit: 5,
          totalPage: 0
        },
        tableList: [],
        deleteProps: [],
        addProps: [],
        isShowSideslider: false,
        sidesliderTitle: '',
        previewData: [],
        isShowInstanceSideslider: false,
        instanceSidesliderTitle: '',
        curIndex: -1,
        curActionIndex: -1,
        curResIndex: -1,
        curGroupIndex: -1,
        originalList: [],
        params: {},
        curScopeAction: {},
        disabled: false,
        authorizationScopeActions: [],
        requestQueue: ['scope', 'group'],
        nextLoading: false,
        isLastPage: false,
        prevLoading: false,
        curCopyParams: {},
        resourceSliderWidth: Math.ceil(window.innerWidth * 0.67 - 7) < 960
          ? 960 : Math.ceil(window.innerWidth * 0.67 - 7)
      };
    },
    computed: {
        ...mapGetters('permTemplate', ['cloneActions']),
        isShowBatchRefer () {
            return payload => {
                return this.cloneActions.some(item => item.action_id === payload.id);
            };
        },
        condition () {
            if (this.curIndex === -1
                || this.curResIndex === -1
                || this.curActionIndex === -1
                || this.curGroupIndex === -1) {
                return [];
            }
            const curData = this.tableList[this.curIndex]
                .add_actions[this.curActionIndex].resource_groups[this.curGroupIndex]
                .related_resource_types[this.curResIndex];

            if (!curData) {
                return [];
            }
            return _.cloneDeep(curData.condition);
        },
        originalCondition () {
            if (this.curIndex === -1
                || this.curResIndex === -1
                || this.curActionIndex === -1
                || this.curGroupIndex === -1
                || this.originalList.length < 1) {
                return [];
            }
            const curId = this.tableList[this.curIndex].add_actions[this.curActionIndex].id;

            const curType = this.tableList[this.curIndex]
                .add_actions[this.curActionIndex]
                .resource_groups[this.curGroupIndex]
                .related_resource_types[this.curResIndex]
                .type;

            if (!this.originalList.some(item => item.add_actions[this.curActionIndex].id === curId)) {
                return [];
            }
            const curData = this.originalList.find(item => item.add_actions[this.curActionIndex].id === curId);
            if (!curData) {
                return [];
            }
            const curActionData = curData.add_actions[this.curActionIndex].resource_groups[this.curGroupIndex];
            if (!curActionData.related_resource_types.some(item => item.type === curType)) {
                return [];
            }
            const curResData = curActionData.related_resource_types.find(item => item.type === curType);
            if (!curResData) {
                return [];
            }
            return _.cloneDeep(curResData.condition);
        },
        curDisabled () {
            if (this.curIndex === -1
                || this.curResIndex === -1
                || this.curActionIndex === -1
                || this.curGroupIndex === -1) {
                return false;
            }
            const curData = this.tableList[this.curIndex]
                .add_actions[this.curActionIndex]
                .resource_groups[this.curGroupIndex]
                .related_resource_types[this.curResIndex];

            return curData.isDefaultLimit;
        },
        curFlag () {
            if (this.curIndex === -1
                || this.curResIndex === -1
                || this.curActionIndex === -1
                || this.curGroupIndex === -1) {
                return 'add';
            }
            const curData = this.tableList[this.curIndex]
                .add_actions[this.curActionIndex]
                .resource_groups[this.curGroupIndex]
                .related_resource_types[this.curResIndex];

            return curData.flag;
        },
        curSelectionMode () {
            if (this.curIndex === -1
                || this.curResIndex === -1
                || this.curActionIndex === -1
                || this.curGroupIndex === -1) {
                return 'all';
            }
            const curData = this.tableList[this.curIndex]
                .add_actions[this.curActionIndex]
                .resource_groups[this.curGroupIndex]
                .related_resource_types[this.curResIndex];

            return curData.selectionMode;
        },
        batchReferAction () {
            return payload => {
                const temp = this.cloneActions.find(item => item.action_id === payload.id);
                if (temp) {
                    return temp.copy_from_actions;
                }
                return [];
            };
        },
        syncLoading () {
            return this.requestQueue.length > 0;
        },
        isAddActionEmpty () {
            return this.addAction.length < 1;
        }
    },
    watch: {
      requestQueue (value) {
        if (value.length < 1) {
          this.$emit('on-ready');
        }
      },
      addAction: {
        handler (value) {
          console.log('value', value);
        },
        immediate: true
      }
    },
    created () {
      this.curCopyKey = '';
      this.fetchData();
      this.fetchAuthorizationScopeActions();
    },
    mounted () {
      this.$once('hook:beforeDestroy', () => {
        window.removeEventListener('resize', this.formatFormItemWidth);
      });
      window.addEventListener('resize', (this.formatFormItemWidth));
    },
    methods: {
      formatFormItemWidth () {
        this.resourceSliderWidth = Math.ceil(window.innerWidth * 0.67 - 7) < 960
          ? 960 : Math.ceil(window.innerWidth * 0.67 - 7);
      },
      
      async fetchData () {
        try {
          const res = await this.$store.dispatch('permTemplate/getGroupsPreview', {
            id: this.id,
            data: {
              limit: this.pagination.limit,
              offset: this.pagination.limit * (this.pagination.current - 1)
            }
          });
          this.pagination.totalPage = Math.ceil(res.data.count / this.pagination.limit);
          this.tableList = _.cloneDeep(res.data.results);
          this.tableList.forEach((item, index) => {
            if (this.addAction.length > 0) {
              this.$set(item, 'add_actions', _.cloneDeep(this.addAction));
              item.add_actions = item.add_actions.map(act => {
                if (!act.resource_groups || !act.resource_groups.length) {
                  act.resource_groups = act.related_resource_types && act.related_resource_types.length ? [{ id: '', related_resource_types: act.related_resource_types }] : [];
                }
                return new SyncPolicy({ ...act, tag: 'add' }, 'add');
              });
            }
            item.delete_actions = item.delete_actions.map(act => {
              if (!act.resource_groups || !act.resource_groups.length) {
                act.resource_groups = act.related_resource_types && act.related_resource_types.length ? [{ id: '', related_resource_types: act.related_resource_types }] : [];
              }
              return new SyncPolicy({ ...act, tag: 'add' }, 'add');
            });
          });
          this.setTableProps();
          this.originalList = _.cloneDeep(this.tableList);
          this.isLastPage = this.pagination.current === this.pagination.totalPage;
          this.$emit('on-all-submit', this.pagination.current === this.pagination.totalPage);
        } catch (e) {
          console.error(e);
          this.messageAdvancedError(e);
        } finally {
          this.requestQueue.shift();
        }
      },

      async fetchAuthorizationScopeActions () {
        try {
          const res = await this.$store.dispatch('permTemplate/getAuthorizationScopeActions', {
            systemId: this.$route.params.systemId
          });
          this.authorizationScopeActions = res.data.filter(item => item.id !== '*');
        } catch (e) {
          console.error(e);
          this.messageAdvancedError(e);
        } finally {
          this.requestQueue.shift();
        }
      },

      getCellClass ({ row, column, rowIndex, columnIndex }) {
        if (columnIndex !== 0) {
          return 'iam-perm-table-cell-cls';
        }
        return '';
      },

      getBacthCopyParms (payload, content) {
        const actions = [];
        this.tableList.forEach(item => {
          item.add_actions.forEach(act => {
            if (act.id !== payload.id) {
              actions.push({
                system_id: this.$route.params.systemId,
                id: act.id
              });
            }
          });
        });
        actions.unshift({
          system_id: this.$route.params.systemId,
          id: payload.id
        });
        return {
          resource_type: {
            system_id: content.system_id,
            type: content.type,
            condition: content.condition.map(item => {
              return {
                id: item.id,
                instances: item.instance || [],
                attributes: item.attribute || []
              };
            })
          },
          actions
        };
      },

      getData () {
        let flag = false;
        let isNoAdd = false;
        const groups = [];
        this.tableList.forEach(groupItem => {
          const actionList = []
          ;(groupItem.add_actions || []).forEach(item => {
            const { type, id, name, environment, description } = item;
            const relatedResourceTypes = [];
            const groupResourceTypes = [];
            if (item.resource_groups.length > 0) {
              item.resource_groups.forEach(groupItem => {
                if (groupItem.related_resource_types.length > 0) {
                  groupItem.related_resource_types.forEach(resItem => {
                    if (resItem.empty) {
                      resItem.isError = true;
                      flag = true;
                    }
                    const conditionList = (resItem.condition.length > 0 && !resItem.empty)
                      ? resItem.condition.map(conItem => {
                        const { id, instance, attribute } = conItem;
                        const attributeList = (attribute && attribute.length > 0)
                          ? attribute.map(({ id, name, values }) => ({ id, name, values }))
                          : [];
        
                        const instanceList = (instance && instance.length > 0)
                          ? instance.map(({ name, type, path, paths }) => {
                            let tempPath = _.cloneDeep(paths);
                            if (!tempPath.length && path && path.length) {
                              tempPath = _.cloneDeep(path);
                            }
                            tempPath.forEach(pathItem => {
                              pathItem.forEach(pathSubItem => {
                                delete pathSubItem.disabled;
                              });
                            });
                            return {
                              name,
                              type,
                              path: tempPath
                            };
                          })
                          : [];
        
                        return {
                          id,
                          instances: instanceList,
                          attributes: attributeList
                        };
                      })
                      : [];
        
                    relatedResourceTypes.push({
                      type: resItem.type,
                      system_id: resItem.system_id,
                      name: resItem.name,
                      condition: conditionList.filter(
                        item => item.instances.length > 0 || item.attributes.length > 0
                      )
                    });
                  });
                }
                groupResourceTypes.push({
                  id: groupItem.id,
                  related_resource_types: relatedResourceTypes
                });
              });
              // 强制刷新下
              item.resource_groups = _.cloneDeep(item.resource_groups);
            }
            const params = {
              type,
              name,
              id,
              description,
              resource_groups: groupResourceTypes,
              environment
            };
            actionList.push(params);
          });
          groups.push({
            id: groupItem.id,
            actions: actionList
          });
        });
        isNoAdd = groups.every(item => item.actions.length < 1);
        return {
          flag,
          groups,
          isNoAdd
        };
      },

      handlePrevPage () {
        window.changeDialog = true;
        if (this.pagination.current > 1) {
          --this.pagination.current;
        }
        this.requestQueue = ['group'];
        this.fetchData();
      },

      async handleNextPage () {
        window.changeDialog = true;
        if (this.isAddActionEmpty) {
          if (this.pagination.current < this.pagination.totalPage) {
            ++this.pagination.current;
            this.requestQueue = ['group'];
            this.fetchData();
          }
          return;
        }
        const { groups, flag } = this.getData();
        if (flag) {
          return;
        }
        this.nextLoading = true;
        try {
          await this.$store.dispatch('permTemplate/preGroupSync', {
            id: this.id,
            data: {
              groups
            }
          });
          if (this.pagination.current < this.pagination.totalPage) {
            ++this.pagination.current;
            this.requestQueue = ['group'];
            this.fetchData();
          }
        } catch (e) {
          console.error(e);
          this.messageAdvancedError(e);
        } finally {
          this.nextLoading = false;
        }
      },

      async handleReferInstance (resItem, act, row, index, $index) {
        window.changeDialog = true;
        act.loading = true;
        try {
          const res = await this.$store.dispatch('permTemplate/getCloneAction', {
            id: this.id,
            data: {
              action_id: act.id,
              clone_from_action_id: resItem.id,
              group_ids: this.tableList.map(item => item.id)
            }
          });
          const referList = res.data;
          this.tableList.forEach(item => {
            const temp = referList.find(sub => sub.group_id === item.id);
            if (temp) {
              item.add_actions.splice(index, 1, new SyncPolicy({ ...temp.policy, tag: 'add' }, 'detail'));
            }
          });
          this.$refs[`popover_${index}_${$index}_ref`][0]
            && this.$refs[`popover_${index}_${$index}_ref`][0].hideHandler();
        } catch (e) {
          console.error(e);
          this.messageAdvancedError(e);
        } finally {
          setTimeout(() => {
            act.loading = false;
          }, 500);
        }
      },

      handleAnimationEnd () {
        this.sidesliderTitle = '';
        this.previewData = [];
      },

      handleShowPopover (payload) {
        payload.showAction = true;
        payload.showPopover = true;
      },

      handleHidePopover (payload) {
        payload.showPopover = false;
      },

      handleCellMouseEnter (row, column, cell, event) {
        if (!row.add_actions) {
          return;
        }
        for (let i = 0; i < row.add_actions.length; i++) {
          if (row.add_actions[i].id === column.property) {
            row.add_actions[i].showAction = true;
            break;
          }
        }
      },

      handleCellMouseLeave (row, column, cell, event) {
        if (!row.add_actions) {
          return;
        }
        for (let i = 0; i < row.add_actions.length; i++) {
          if (row.add_actions[i].id === column.property && !row.add_actions[i].showPopover) {
            row.add_actions[i].showAction = false;
            break;
          }
        }
      },

      showMessage (payload) {
        this.bkMessageInstance = this.$bkMessage({
          limit: 1,
          theme: 'success',
          message: payload
        });
      },

      handleOnInit (payload) {
        this.disabled = !payload;
      },

      resetDataAfterClose () {
        this.curIndex = -1;
        this.curResIndex = -1;
        this.curActionIndex = -1;
        this.curGroupIndex = -1;
        this.params = {};
        this.instanceSidesliderTitle = '';
      },

      handleResourceCancel (payload) {
        const typeMap = {
          mask: () => {
            const { data } = this.$refs.renderResourceRef.handleGetValue();
            const { hasSelectedCondition } = this.$refs.renderResourceRef;
            let cancelHandler = Promise.resolve();
            if (JSON.stringify(data) !== JSON.stringify(hasSelectedCondition)) {
              cancelHandler = leaveConfirm();
            }
            cancelHandler.then(() => {
              this.isShowInstanceSideslider = false;
              this.resetDataAfterClose();
            }, _ => _);
          },
          cancel: () => {
            this.resetDataAfterClose();
            this.isShowInstanceSideslider = false;
          }
        };
        return typeMap[payload]();
      },

      handleResourceSubmit () {
        const conditionData = this.$refs.renderResourceRef.handleGetValue();
        const { isEmpty, data } = conditionData;
        if (isEmpty) {
          return;
        }
        window.changeAlert = false;
        this.instanceSidesliderTitle = '';
        this.isShowInstanceSideslider = false;
        const resItem = this.tableList[this.curIndex]
          .add_actions[this.curActionIndex]
          .resource_groups[this.curGroupIndex]
          .related_resource_types[this.curResIndex];

        const isConditionEmpty = data.length === 1 && data[0] === 'none';
        if (isConditionEmpty) {
          resItem.condition = ['none'];
        } else {
          resItem.condition = data;
          resItem.isError = false;
        }

        this.curIndex = -1;
        this.curResIndex = -1;
        this.curActionIndex = -1;
        this.curGroupIndex = -1;
        window.changeDialog = true;
      },

      handlerConditionMouseover (payload, row) {
        if (Object.keys(this.curCopyParams).length < 1) {
          return;
        }

        if (this.curCopyKey === `${payload.system_id}${payload.type}`) {
          payload.canPaste = true;
        }
      },

      handlerConditionMouseleave (payload) {
        payload.canPaste = false;
      },

      handlerOnCopy (payload, $index, subIndex, index, action) {
        window.changeDialog = true;
        this.curCopyKey = `${payload.system_id}${payload.type}`;
        this.curCopyParams = this.getBacthCopyParms(action, payload);
        this.showMessage(this.$t(`m.info['实例复制']`));
        this.$refs[`condition_${index}_${$index}_${subIndex}_ref`][0]
          && this.$refs[`condition_${index}_${$index}_${subIndex}_ref`][0].setImmediatelyShow(true);
      },

      handlerOnPaste (payload, content) {
        if (!payload.flag) {
          return;
        }
        if (payload.data.length === 0) {
          content.condition = [];
        } else {
          content.condition = payload.data.map(conditionItem => new Condition(conditionItem, '', 'add'));
        }
        content.isError = false;
        this.showMessage(this.$t(`m.info['粘贴成功']`));
      },

      handlerOnBatchPaste (payload, content, $index, subIndex, index) {
        if (!payload.flag) {
          return;
        }
        if (payload.data.length === 0) {
          this.tableList.forEach(item => {
            item.add_actions.forEach(subItem => {
              subItem.related_resource_types.forEach(resItem => {
                if (`${resItem.system_id}${resItem.type}` === this.curCopyKey) {
                  resItem.condition = [];
                  resItem.isError = false;
                }
              });
            });
          });
        } else {
          this.tableList.forEach(item => {
            item.add_actions.forEach(subItem => {
              const curPasteData = payload.data.find(_ => _.id === subItem.id);
              if (curPasteData) {
                // subItem.related_resource_types.forEach(resItem => {
                //   if (`${resItem.system_id}${resItem.type}` === `${curPasteData.resource_type.system_id}${curPasteData.resource_type.type}`) {
                //     resItem.condition = curPasteData.resource_type.condition.map(conditionItem => new Condition(conditionItem, '', 'add'));
                //     resItem.isError = false;
                //     resItem.isEmpty = false;
                //   }
                // });
                subItem.resource_groups && subItem.resource_groups.forEach(groupItem => {
                  groupItem.related_resource_types.forEach(subItem => {
                    if (`${subItem.system_id}${subItem.type}` === this.curCopyKey) {
                      subItem.condition = curPasteData.resource_type.condition.map(conditionItem => new Condition(conditionItem, '', 'add'));
                      subItem.isError = false;
                    }
                  });
                });
              }
            });
          });
        }
        this.curCopyParams = {};
        content.isError = false;
        this.$refs[`condition_${index}_${$index}_${subIndex}_ref`][0]
          && this.$refs[`condition_${index}_${$index}_${subIndex}_ref`][0].setImmediatelyShow(false);
        this.showMessage(this.$t(`m.info['批量粘贴成功']`));
      },

      showResourceInstance (data, resItem, resIndex, $index, index, groupIndex) {
        this.params = {
          system_id: this.$route.params.systemId,
          action_id: data.add_actions[index].id,
          resource_type_system: resItem.system_id,
          resource_type_id: resItem.type
        };
        this.curScopeAction = this.authorizationScopeActions.find(
          item => item.id === data.add_actions[index].id
        );

        console.log('this.curScopeAction', this.curScopeAction);
        this.curIndex = $index;
        this.curActionIndex = index;
        this.curResIndex = resIndex;
        this.curGroupIndex = groupIndex;
        this.instanceSidesliderTitle = this.$t(`m.info['关联侧边栏操作的资源实例']`, { value: `${this.$t(`m.common['【']`)}${data.add_actions[index].name}${this.$t(`m.common['】']`)}` });
        window.changeAlert = 'iamSidesider';
        this.isShowInstanceSideslider = true;
      },

      handleViewResource (payload, index, groIndex) {
        const data = payload.delete_actions[index].resource_groups[groIndex];
        const params = [];
        if (data.related_resource_types.length > 0) {
          data.related_resource_types.forEach(item => {
            const { name, type, condition } = item;
            params.push({
              name: type,
              label: this.$t(`m.info['tab操作实例']`, { value: name }),
              tabType: 'resource',
              data: condition
            });
          });
        }
        this.previewData = params;
        this.sidesliderTitle = this.$t(`m.info['操作侧边栏操作的资源实例']`, { value: `${this.$t(`m.common['【']`)}${payload.name}${this.$t(`m.common['】']`)}` });
        this.isShowSideslider = true;
      },

      renderDeleteActionHeader (h, { column }) {
        return h(
          'div', {
            class: {
              'sync-action-label': true
            },
            attrs: {
              title: column.label
            }
          },
          [
            h('bk-tag', {
              style: {
                margin: '0 4px 0 0'
              },
              props: {
                theme: 'danger'
              },
              domProps: {
                innerHTML: this.$t(`m.common['移除']`)
              }
            }),
            h('span', {
              domProps: {
                innerHTML: column.label
              }
            })
          ]
        );
      },

      renderAddActionHeader (h, { column }) {
        return h(
          'div', {
            class: {
              'sync-action-label': true
            },
            attrs: {
              title: column.label
            }
          },
          [
            h('bk-tag', {
              style: {
                margin: '0 4px 0 0'
              },
              props: {
                theme: 'info'
              },
              domProps: {
                innerHTML: this.$t(`m.common['新增']`)
              }
            }),
            h('span', {
              domProps: {
                innerHTML: column.label
              }
            })
          ]
        );
      },

      setTableProps () {
        this.addProps = [];
        this.deleteProps = [];
        this.addAction.forEach(item => {
          this.addProps.push({
            label: item.name,
            id: item.id
          });
        });
        if (this.tableList.some(item => item.delete_actions.length > 0)) {
          this.tableList[0].delete_actions.forEach(item => {
            this.deleteProps.push({
              label: item.name,
              id: item.id
            });
          });
        }
      }
    }
  };
</script>
<style lang="postcss">
    .iam-template-sync-wrapper {
        min-height: 200px;
        .iam-template-sync-table-cls {
            border-bottom: 0;
            .relation-content-wrapper {
                height: 100%;
                padding: 17px 0;
                color: #63656e;
                .resource-type-name {
                    display: block;
                    margin-bottom: 9px;
                }
            }
            .related-resource-item {
                cursor: pointer;
                &:hover {
                    color: #3a84ff;
                }
            }
            .relation-content-item {
                margin-top: 17px;
                &:first-child {
                    margin-top: 0;
                }
                &.reset-margin-top {
                    margin-top: 10px;
                }
                .content-name {
                    margin-bottom: 9px;
                }
            }
            .iam-template-sync-popover-cls {
                position: absolute;
                top: 5px;
                right: 5px;
                cursor: pointer;
                &:hover {
                    color: #3a84ff;
                }
            }
            .sync-action-label {
                max-width: 170px;
                overflow: hidden;
                text-overflow: ellipsis;
                word-break: break-all;
            }
        }
    }
    .pagination-wrapper {
        margin-top: 16px;
        text-align: center;
        .page-display {
            display: inline-block;
            width: 74px;
            height: 32px;
            line-height: 32px;
            border: 1px solid #c4c6cc;
            border-radius: 2px;
            vertical-align: bottom;
        }
    }
    .sync-popover-content {
        max-height: 250px;
        overflow-y: auto;
        &::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        &::-webkit-scrollbar-thumb {
            background: #dcdee5;
            border-radius: 3px;
        }
        &::-webkit-scrollbar-track {
            background: transparent;
            border-radius: 3px;
        }
        .cursor {
            line-height: 24px;
            color: #63656e;
            cursor: pointer;
            &:hover {
                color: #3a84ff;
            }
            &.disabled {
                color: #c4c6cc;
                cursor: not-allowed;
                &:hover {
                    color: #c4c6cc;
                }
            }
        }
        p.refer-title {
            line-height: 24px;
            color: #313238;
        }
    }
</style>
