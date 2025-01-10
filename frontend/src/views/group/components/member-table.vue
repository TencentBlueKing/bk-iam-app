<template>
  <div class="iam-user-group-member">
    <render-search>
      <div class="flex-between group-member-button">
        <div class="group-member-button-item">
          <bk-button :disabled="readOnly" @click="handleAddMember">
            {{ $t(`m.userGroup['添加成员']`) }}
          </bk-button>
        </div>
        <div class="group-member-button-item">
          <bk-dropdown-menu
            ref="batchDropdown"
            :disabled="isBatchDisabled"
            @show="handleDropdownShow"
            @hide="handleDropdownHide"
          >
            <div class="group-dropdown-trigger-btn" slot="dropdown-trigger">
              <span class="group-dropdown-text">{{ $t(`m.common['批量处理']`) }}</span>
              <i :class="['bk-icon icon-angle-down', { 'icon-flip': isDropdownShow }]" />
            </div>
            <ul class="bk-dropdown-list" slot="dropdown-content">
              <li>
                <a
                  :class="[{ 'remove-disabled': isNoBatchDelete() }]"
                  :title="adminGroupTitle"
                  @click.stop="handleBatchProcess('remove')"
                >
                  {{ $t(`m.common['批量移除']`) }}
                </a>
              </li>
              <li v-if="!['memberTemplate'].includes(routeMode)">
                <a
                  :class="[{ 'renewal-disabled': isNoBatchRenewal() }]"
                  :title="renewalGroupTitle"
                  @click.stop="handleBatchProcess('renewal')"
                >
                  {{ $t(`m.renewal['批量续期']`) }}
                </a>
              </li>
            </ul>
          </bk-dropdown-menu>
        </div>
        <div class="group-member-button-item" @mouseenter="handleCascadeEnter">
          <bk-cascade
            ref="copyCascade"
            v-model="copyValue"
            :list="COPY_KEYS_ENUM"
            :clearable="false"
            :ext-popover-cls="
              !curLanguageIsCn
                ? 'copy-user-group-cls copy-user-group-cls-lang'
                : 'copy-user-group-cls'
            "
            :disabled="isCopyDisabled"
            :placeholder="$t(`m.userGroup['复制成员']`)"
            :trigger="'hover'"
            :style="{ width: curLanguageIsCn ? '100px' : '140px' }"
          >
            <div slot="option" slot-scope="{ node }">
              <div
                class="cascade-custom-content"
                @click="handleTriggerCopy(...arguments, node)">
                {{ node.name }}
              </div>
            </div>
          </bk-cascade>
        </div>
      </div>
      <div slot="right">
        <bk-input
          v-model="keyword"
          style="width: 400px"
          :placeholder="searchPlaceholder"
          :clearable="true"
          @clear="handleKeyWordClear"
          @enter="handleKeyWordEnter"
        />
      </div>
    </render-search>
    <div class="group-member-wrapper">
      <bk-tab
        v-if="isExistMemberTemplate"
        ref="tabRef"
        :active.sync="tabActive"
        type="unborder-card"
        ext-cls="group-tab-wrapper"
        @tab-change="handleTabChange"
      >
        <bk-tab-panel v-for="panel in groupTabList" v-bind="panel" :key="panel.name">
          <template slot="label">
            <span class="panel-name">{{ panel.label }}</span>
            <span
              :class="['panel-count', { 'panel-count-active': tabActive === panel.name }]"
            >
              {{ panel.count }}
            </span>
          </template>
        </bk-tab-panel>
      </bk-tab>

      <bk-table
        ref="groupMemberRef"
        size="small"
        ext-cls="user-group-member-table"
        :data="getTableList()"
        :cell-class-name="getCellClass"
        :outer-border="false"
        :header-border="false"
        :pagination="formatPagination()"
        @page-change="handlePageChange"
        @page-limit-change="handleLimitChange"
        @select="handlerChange"
        @select-all="handlerAllChange"
        v-bkloading="{ isLoading: tableLoading, opacity: 1 }"
      >
        <bk-table-column type="selection" align="center" :selectable="getDefaultSelect" />
        <template v-for="item in renderTableColumn">
          <template v-if="item.prop === 'name'">
            <bk-table-column
              :key="item.prop"
              :label="item.label"
              :prop="item.prop">
              <template slot-scope="{ row }">
                <div
                  v-if="row.type === 'user'"
                  class="user"
                  :title="`${row.id}(${row.name})`"
                >
                  <Icon type="personal-user" />
                  <span class="name">{{ row.id }}</span
                  ><span class="count" v-if="row.name">
                    {{ "(" + row.name + ")" }}
                  </span>
                </div>
                <div v-else
                  class="depart"
                  :title="row.full_name"
                >
                  <Icon type="organization-fill" />
                  <span class="name" :style="{ maxWidth: curDisplaySet.customNameWidth }">
                    {{ row.name || "--" }}
                  </span>
                  <span class="count" v-if="row.member_count && enableOrganizationCount">
                    ({{ row.member_count }})
                  </span>
                </div>
              </template>
            </bk-table-column>
          </template>
          <template v-else-if="item.prop === 'template_name'">
            <bk-table-column
              :key="item.prop"
              :label="item.label"
              :prop="item.prop">
              <template slot-scope="{ row }">
                <div class="member-template" :title="row.name" @click.stop="handleTempView(row)">
                  <Icon type="renyuanmuban" />
                  <span class="name">
                    {{ row.name || "--" }}
                  </span>
                </div>
              </template>
            </bk-table-column>
          </template>
          <template v-else-if="item.prop === 'user_departments'">
            <bk-table-column
              :key="item.prop"
              :label="item.label"
              :prop="item.prop">
              <template slot-scope="{ row }">
                <template v-if="row.type === 'user'">
                  <template v-if="row.user_departments && row.user_departments.length">
                    <div
                      :title="row.user_departments.join(';')"
                      v-for="(v, i) in row.user_departments"
                      :key="i"
                      class="user_departs"
                    >
                      {{ v }}
                    </div>
                  </template>
                  <template v-else>
                    <div>--</div>
                  </template>
                </template>
                <template v-else>
                  {{ row.full_name }}
                </template>
              </template>
            </bk-table-column>
          </template>
          <template v-else-if="item.prop === 'expired_at_display' && !['memberTemplate'].includes(routeMode)">
            <bk-table-column
              :key="item.prop"
              :label="item.label"
              :prop="item.prop"
              :render-header="renderHeader"
            />
          </template>
          <template v-else-if="item.prop === 'created_time'">
            <bk-table-column
              :key="item.prop"
              :label="item.label"
              :prop="item.prop">
              <template slot-scope="{ row }">
                <span :title="row.created_time.replace(/T/, ' ')">
                  {{ row.created_time.replace(/T/, " ") }}
                </span>
              </template>
            </bk-table-column>
          </template>
          <template v-else-if="item.prop === 'operate'">
            <bk-table-column
              :key="item.prop"
              :label="item.label"
              :prop="item.prop"
              :width="curLanguageIsCn ? 100 : 150"
              :fixed="'right'"
            >
              <template slot-scope="{ row }">
                <template v-if="['memberTemplate'].includes(routeMode)">
                  <bk-button
                    text
                    theme="primary"
                    :disabled="disabledTempGroup()"
                    :title="disabledTempGroup() ? $t(`m.memberTemplate['只读人员模板不能移除']`) : ''"
                    @click="handleDelete(row)"
                  >
                    {{ $t(`m.common['移除']`) }}
                  </bk-button>
                </template>
                <template v-else>
                  <bk-button
                    text
                    theme="primary"
                    :disabled="disabledGroup()"
                    :title="disabledGroup() ? $t(`m.userGroup['管理员组至少保留一条数据']`) : ''"
                    @click="handleDelete(row)"
                  >
                    {{ $t(`m.common['移除']`) }}
                  </bk-button>
                  <bk-button
                    v-if="row.expired_at !== PERMANENT_TIMESTAMP"
                    theme="primary"
                    style="margin-left: 5px"
                    text
                    @click="handleShowRenewal(row)"
                  >
                    {{ $t(`m.renewal['续期']`) }}
                  </bk-button>
                </template>
              </template>
            </bk-table-column>
          </template>
          <template v-else>
            <bk-table-column
              :key="item.prop"
              :label="item.label"
              :prop="item.prop"
            >
              <template slot-scope="{ row }">
                <span :title="row">
                  {{ row[item.prop] || '--' }}
                </span>
              </template>
            </bk-table-column>
          </template>
        </template>
        <template slot="empty">
          <ExceptionEmpty
            :type="emptyData.type"
            :empty-text="emptyData.text"
            :tip-text="emptyData.tip"
            :tip-type="emptyData.tipType"
            @on-clear="handleEmptyClear"
            @on-refresh="handleEmptyRefresh"
          />
        </template>
      </bk-table>
    </div>

    <delete-dialog
      :show.sync="deleteDialog.visible"
      :loading="deleteDialog.loading"
      :title="deleteDialog.title"
      :sub-title="deleteDialog.subTitle"
      @on-after-leave="handleAfterDeleteLeave"
      @on-cancel="hideCancelDelete"
      @on-sumbit="handleSubmitDelete"
    />

    <add-member-dialog
      :show.sync="isShowAddMemberDialog"
      :loading="loading"
      :name="name"
      :id="id"
      :show-expired-at="showExpiredAt"
      :is-rating-manager="isRatingManager"
      :route-mode="routeMode"
      @on-cancel="handleCancelAdd"
      @on-sumbit="handleSubmitAdd"
      @on-after-leave="handleAddAfterClose"
    />

    <render-renewal-dialog
      :show.sync="isShowRenewalDialog"
      :data="curData"
      :type="curType"
      :list="currentSelectList"
      :loading="renewalLoading"
      @on-submit="handleRenewalSubmit"
    />

    <MemberTemplateDetailSlider
      :show.sync="isShowTempDetailSlider"
      :cur-detail-data="curTempData"
    />
  </div>
</template>
<script>
  import _ from 'lodash';
  import il8n from '@/language';
  import ClipboardJS from 'clipboard';
  import { mapGetters } from 'vuex';
  import { PERMANENT_TIMESTAMP, COPY_KEYS_ENUM } from '@/common/constants';
  import { formatCodeData } from '@/common/util';
  import { bus } from '@/common/bus';
  import renderRenewalDialog from '@/components/render-renewal-dialog';
  import DeleteDialog from '../common/iam-confirm-dialog';
  import AddMemberDialog from './iam-add-member';
  import MemberTemplateDetailSlider from '@/views/group/components/member-template-detail-slider';

  export default {
    inject: {
      getGroupAttributes: { value: 'getGroupAttributes', default: null }
    },
    components: {
      DeleteDialog,
      AddMemberDialog,
      renderRenewalDialog,
      MemberTemplateDetailSlider
    },
    props: {
      id: {
        type: [String, Number],
        default: ''
      },
      name: {
        type: String,
        default: ''
      },
      count: {
        type: Number,
        default: 0
      },
      data: {
        type: Array,
        default: () => []
      },
      readOnly: {
        type: Boolean,
        default: false
      },
      isShowTab: {
        type: Boolean,
        default: true
      },
      searchPlaceholder: {
        type: String,
        default: il8n('userGroupDetail', '请输入用户/组织或人员模板，按enter键搜索')
      },
      routeMode: {
        type: String,
        default: ''
      },
      displaySet: {
        type: Object
      },
      curDetailData: {
        type: Object
      },
      showExpiredAt: {
        type: Boolean,
        default: false
      }
    },
    data () {
      return {
        tableList: [],
        tableLoading: false,
        isMouseCascadeEnter: false,
        currentSelectList: [],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        userOrOrgPagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        memberPagination: {
          current: 1,
          count: 0,
          limit: 10,
          showTotalCount: true
        },
        currentBackup: 1,
        deleteDialog: {
          visible: false,
          title: this.$t(`m.dialog['确认移除']`),
          subTitle: '',
          loading: false
        },
        curMember: {},
        curData: {},
        curDisplaySet: {},
        loading: false,
        isShowAddMemberDialog: false,
        isShowRenewalDialog: false,
        isShowTempDetailSlider: false,
        renewalLoading: false,
        emptyData: {
          type: '',
          text: '',
          tip: '',
          tipType: ''
        },
        emptyOrgData: {
          type: '',
          text: '',
          tip: '',
          tipType: ''
        },
        emptyTempData: {
          type: '',
          text: '',
          tip: '',
          tipType: ''
        },
        adminGroupTitle: '',
        renewalGroupTitle: '',
        keyword: '',
        enableOrganizationCount: window.ENABLE_ORGANIZATION_COUNT.toLowerCase() === 'true',
        isDropdownShow: false,
        copyValue: [],
        curCopyCascade: {},
        PERMANENT_TIMESTAMP,
        COPY_KEYS_ENUM,
        externalRoutes: ['userGroupDetail', 'memberTemplate'],
        groupTabList: [
          {
            name: 'userOrgPerm',
            label: this.$t(`m.userGroup['用户/组织']`),
            count: 0,
            empty: 'emptyOrgData',
            tableList: []
          },
          {
            name: 'memberTemplate',
            label: this.$t(`m.nav['人员模板']`),
            count: 0,
            empty: 'emptyTempData',
            tableList: []
          }
        ],
        tabActive: 'userOrgPerm',
        copyUrl: 'userGroup/getUserGroupMemberList',
        curRouteMode: '',
        curTempData: {},
        curModeMap: {
          memberTemplate: {
            list: {
              url: 'memberTemplate/getSubjectTemplateMembers',
              params: {}
            },
            removeMember: {
              dialogTitle: '确认移除该用户/组织？',
              url: 'memberTemplate/deleteSubjectTemplateMembers',
              params: {
                subjects: []
              }
            },
            addMember: {
              url: 'memberTemplate/addSubjectTemplateMembers',
              params: {
                subjects: []
              }
            },
            copy: {
              url: 'memberTemplate/getSubjectTemplateMembers'
            }
          }
        },
        tableProps: [],
        userOrOrgCount: 0
      };
    },
    computed: {
      ...mapGetters(['user', 'externalSystemId']),
      isNoBatchDelete () {
        return () => {
          const hasData = this.currentSelectList.length > 0;
          if (
            hasData
            && ['userOrgPerm'].includes(this.tabActive)
            && this.getGroupAttributes
            && this.getGroupAttributes().source_from_role
          ) {
            const isAll = hasData && this.currentSelectList.length === this.userOrOrgCount;
            this.adminGroupTitle = isAll
              ? this.$t(`m.userGroup['管理员组至少保留一条数据']`)
              : '';
            return isAll;
          }
          return !hasData;
        };
      },
      isNoBatchRenewal () {
        return () => {
          const emptyField = this.groupTabList.find((item) => item.name === this.tabActive);
          if (emptyField) {
            const hasData = emptyField.tableList.length > 0 && this.currentSelectList.length > 0;
            if (hasData) {
              this.selectNoRenewalList = this.currentSelectList.filter(
                (item) => item.expired_at === PERMANENT_TIMESTAMP
              );
              if (this.currentSelectList.length === this.selectNoRenewalList.length) {
                this.renewalGroupTitle = this.$t(
                  `m.userGroup['已选择的用户组成员不需要续期']`
                );
                return true;
              }
            }
            return !hasData;
          }
        };
      },
      isRatingManager () {
        return ['rating_manager', 'subset_manager'].includes(this.user.role.type);
      },
      curType () {
        return this.curData.type || 'department';
      },
      disabledGroup () {
        return () => {
          return (
            this.getGroupAttributes
            && this.getGroupAttributes().source_from_role
            && (this.userOrOrgCount === 1 || (this.userOrOrgCount === this.userOrOrgPagination.count === 1))
            && (['userOrgPerm'].includes(this.tabActive) && !this.routeMode)
          );
        };
      },
      disabledTempGroup () {
        return () => {
          return this.readOnly;
        };
      },
      isBatchDisabled () {
        return ['memberTemplate'].includes(this.routeMode) ? this.readOnly : !this.currentSelectList.length;
      },
      isCopyDisabled () {
        return this.readOnly || (!this.groupTabList[0].tableList.length);
      },
      formatPagination () {
        return () => {
          const typeMap = {
            userOrgPerm: () => {
              return this.userOrOrgPagination;
            },
            memberTemplate: () => {
              return this.memberPagination;
            }
          };
          return typeMap[this.tabActive]();
        };
      },
      getTableList () {
        return () => {
          const [userOrgPerm, memberTemplate] = this.groupTabList;
          const typeMap = {
            userOrgPerm: () => {
              return userOrgPerm.tableList;
            },
            memberTemplate: () => {
              return memberTemplate.tableList;
            }
          };
          return typeMap[this.tabActive]();
        };
      },
      renderTableColumn () {
        return this.tableProps.filter((v) => v.visible);
      },
      isAdminGroup () {
          return this.getGroupAttributes && this.getGroupAttributes().source_from_role;
      },
      isShowMemberTemplate () {
          return !['staff'].includes(this.user.role.type) && !this.isAdminGroup;
      },
      // 蓝盾场景
      isShowExternalMemberTemplate () {
        return !['staff', 'rating_manager'].includes(this.user.role.type) && !this.isAdminGroup;
      },
      isExistMemberTemplate () {
        return this.externalSystemId
        ? this.isShowTab && this.isShowExternalMemberTemplate : this.isShowTab && this.isShowMemberTemplate;
      }
    },
    watch: {
      'userOrOrgPagination.current' (value) {
        this.currentBackup = value;
      },
      data: {
        handler (value) {
          this.groupTabList[0].tableList.splice(0, this.groupTabList[0].tableList.length, ...value);
        },
        immediate: true
      },
      count: {
        handler (value) {
          this.userOrOrgPagination.count = value;
        },
        immediate: true
      },
      displaySet: {
        handler (value) {
          this.curDisplaySet = Object.assign({}, value);
        },
        immediate: true
      },
      tabActive: {
        handler (newValue, oldValue) {
          this.curRouteMode = ['userOrgPerm'].includes(newValue) ? 'userGroupDetail' : newValue;
          if (this.routeMode) {
            this.curRouteMode = _.cloneDeep(this.routeMode);
          }
          this.tableProps = Object.freeze(this.getTableProps(newValue));
          if (oldValue && oldValue !== newValue) {
            this.resetPagination();
          }
        },
        immediate: true
      }
    },
    created () {
      this.fetchInitData();
    },
    methods: {
      renderHeader (h, data) {
        const directive = {
          name: 'bkTooltips',
          content: this.$t(`m.userGroupDetail['该有效期为模板里成员的默认有效期，实际有效期以成员有效期为准']`),
          placement: 'top'
        };
        return ['memberTemplate'].includes(this.tabActive)
          ? <a class="custom-expired-header-cell" v-bk-tooltips={ directive }>{ data.column.label }</a>
          : <a>{ data.column.label }</a>;
      },

      getTableProps (payload) {
        const tabMap = {
          userOrgPerm: () => {
            return [
              { label: this.$t(`m.userGroup['用户/组织']`), prop: 'name' },
              { label: this.$t(`m.userGroupDetail['所属组织架构']`), prop: 'user_departments' },
              { label: this.$t(`m.common['有效期']`), prop: 'expired_at_display' },
              { label: this.$t(`m.common['备注']`), prop: 'description' },
              { label: this.$t(`m.common['加入时间']`), prop: 'created_time' },
              { label: this.$t(`m.perm['加入方式']`), prop: 'join_method' },
              { label: this.$t(`m.common['操作-table']`), prop: 'operate' }
            ].map((v) => {
              let result = true;
              if (['join_method'].includes(v.prop) && !['userGroupDetail'].includes(this.$route.name)) {
                result = false;
              }
              return {
                ...v,
                ...{
                  visible: result
                }
              };
            });
          },
          memberTemplate: () => {
            return [
              { label: this.$t(`m.memberTemplate['人员模板']`), prop: 'template_name' },
              { label: this.$t(`m.common['有效期']`), prop: 'expired_at_display' },
              { label: this.$t(`m.common['备注']`), prop: 'description' },
              { label: this.$t(`m.common['加入时间']`), prop: 'created_time' },
              { label: this.$t(`m.common['操作-table']`), prop: 'operate' }
            ].map((v) => {
              return {
                ...v,
                ...{
                  visible: true
                }
              };
            });
          }
        };
        return tabMap[payload]();
      },

      getDefaultSelect () {
        const [userOrgPerm, memberTemplate] = this.groupTabList;
        const typeMap = {
          userOrgPerm: () => {
            return userOrgPerm.tableList.length > 0;
          },
          memberTemplate: () => {
            return memberTemplate.tableList.length > 0;
          }
        };
        return typeMap[this.tabActive];
      },

      getCellClass ({ row, column, rowIndex, columnIndex }) {
        if (columnIndex === 2) {
          return 'iam-table-cell-depart-cls';
        }
        return '';
      },

      fetchInitData () {
        this.fetchMemberList();
      },

      fetchMemberList () {
        this.fetchUserOrOrgList();
        if (this.isExistMemberTemplate) {
          this.fetchMemberTemplateList();
        }
      },

      async fetchUserOrOrgList () {
        this.tableLoading = true;
        try {
          const { current, limit } = this.userOrOrgPagination;
          const params = {
            id: this.id,
            limit,
            offset: limit * (current - 1),
            keyword: this.keyword
          };
          let url = 'userGroup/getUserGroupMemberList';
          if (this.curModeMap[this.routeMode]) {
            url = this.curModeMap[this.routeMode].list.url;
          }
          const { code, data } = await this.$store.dispatch(
            url,
            params
          );
          const { count, results } = data;
          this.$set(this.groupTabList[0], 'tableList', results || []);
          this.userOrOrgPagination.count = count || 0;
          // 处理蓝盾管理员组业务，搜索只有一条实际有多条数据
          if (!this.keyword) {
            this.userOrOrgCount = count || 0;
          }
          this.emptyOrgData = formatCodeData(code, this.emptyOrgData, this.groupTabList[0].tableList.length === 0);
          if (this.keyword) {
            if (!data.hasOwnProperty('count')) {
              this.userOrOrgPagination.count = this.groupTabList[0].tableList.length;
            }
            this.emptyOrgData = Object.assign(this.emptyOrgData, { tipType: 'search' });
          }
          this.fetchRefreshSelectList();
        } catch (e) {
          console.error(e);
          this.$set(this.groupTabList[0], 'tableList', []);
          this.userOrOrgPagination.count = 0;
          this.userOrOrgCount = 0;
          this.emptyOrgData = formatCodeData(e.code, this.emptyOrgData);
          this.handleRefreshTabCount();
          this.messageAdvancedError(e);
        } finally {
          this.tableLoading = false;
          const emptyField = this.groupTabList.find(item => item.name === this.tabActive);
          if (emptyField) {
            this.emptyData = formatCodeData(0, _.cloneDeep(Object.assign(this[emptyField.empty], { tipType: this.keyword ? 'search' : '' })));
          }
        }
      },

      async fetchMemberTemplateList () {
        this.tableLoading = true;
        try {
          const { current, limit } = this.memberPagination;
          const params = {
            id: this.id,
            page: current,
            page_size: limit,
            name: this.keyword
          };
          const { code, data } = await this.$store.dispatch(
            'memberTemplate/getGroupSubjectTemplate',
            params
          );
          const { count, results } = data;
          this.$set(this.groupTabList[1], 'tableList', results || []);
          this.memberPagination.count = count || 0;
          if (this.keyword) {
            if (!data.hasOwnProperty('count')) {
              this.memberPagination.count = this.groupTabList[1].tableList.length;
            }
            this.emptyOrgData = Object.assign(this.emptyOrgData, { tipType: 'search' });
          }
          this.emptyTempData = formatCodeData(code, this.emptyTempData, this.memberPagination.count === 0);
          this.fetchRefreshSelectList();
        } catch (e) {
          console.error(e);
          this.$set(this.groupTabList[1], 'tableList', []);
          this.memberPagination.count = 0;
          this.emptyTempData = formatCodeData(e.code, this.emptyTempData);
          this.messageAdvancedError(e);
          this.handleRefreshTabCount();
        } finally {
          this.tableLoading = false;
          const emptyField = this.groupTabList.find(item => item.name === this.tabActive);
          if (emptyField) {
            this.emptyData = _.cloneDeep(Object.assign(this[emptyField.empty], { tipType: this.keyword ? 'search' : '' }));
          }
        }
      },

      async handleKeyWordEnter () {
        this.resetPagination();
        this.fetchInitData();
      },

      async handleKeyWordClear () {
        await this.handleEmptyRefresh();
      },

      async handleTabChange (payload) {
        this.tabActive = payload;
        this.handleRefreshTab();
      },

      handleRefreshTab () {
        this.curMember = {};
        this.currentSelectList = [];
        this.$set(this.groupTabList[0], 'tableList', []);
        this.$set(this.groupTabList[1], 'tableList', []);
        this.resetPagination();
        const tabMap = {
          userOrgPerm: async () => {
            await this.fetchUserOrOrgList();
          },
          memberTemplate: async () => {
            await this.fetchMemberTemplateList();
          }
        };
        return tabMap[this.tabActive]();
      },

      handleTempView (payload) {
        this.curTempData = Object.assign({}, {
          ...payload,
          id: this.id,
          template_id: payload.id
        });
        this.isShowTempDetailSlider = true;
      },

      handleRefreshTabCount () {
        this.$nextTick(() => {
          this.$set(this.groupTabList[0], 'count', this.userOrOrgPagination.count || 0);
          this.$set(this.groupTabList[1], 'count', this.memberPagination.count || 0);
          this.$refs.tabRef
            && this.$refs.tabRef.$refs.tabLabel
            && this.$refs.tabRef.$refs.tabLabel.forEach((label) => label.$forceUpdate());
        });
      },

      async fetchRefreshSelectList () {
        const emptyField = this.groupTabList.find(item => item.name === this.tabActive);
        if (emptyField) {
          this.$nextTick(() => {
            const currentSelectList = this.currentSelectList.map((item) => item.id.toString());
            emptyField.tableList.forEach((item) => {
              if (['memberTemplate'].includes(this.tabActive)) {
                this.$set(item, 'type', 'template');
              }
              if (currentSelectList.includes(item.id.toString())) {
                this.$refs.groupMemberRef
                  && this.$refs.groupMemberRef.toggleRowSelection(item, true);
              }
            });
            if (!this.currentSelectList.length) {
              this.$refs.groupMemberRef && this.$refs.groupMemberRef.clearSelection();
            }
          });
          await this.handleRefreshTabCount();
          await this.fetchCustomTotal();
        }
      },

      fetchCustomTotal () {
        this.$nextTick(() => {
          const tableRef = this.$refs.groupMemberRef;
          if (tableRef && tableRef.$refs && tableRef.$refs.paginationWrapper) {
            const paginationWrapper = tableRef.$refs.paginationWrapper;
            const selectCount = paginationWrapper.getElementsByClassName('bk-page-selection-count');
            if (selectCount && selectCount.length && selectCount[0].children) {
              selectCount[0].children[0].innerHTML = this.currentSelectList.length;
            }
          }
        });
      },

      fetchSelectedGroups (type, payload, row) {
        const typeMap = {
          multiple: async () => {
            const isChecked = payload.length && payload.indexOf(row) !== -1;
            if (isChecked) {
              this.currentSelectList.push(row);
            } else {
              this.currentSelectList = this.currentSelectList.filter(
                (item) => item.id.toString() !== row.id.toString()
              );
            }
            await this.fetchCustomTotal();
          },
          all: async () => {
            const emptyField = this.groupTabList.find((item) => item.name === this.tabActive);
            if (emptyField) {
              const tableList = _.cloneDeep(emptyField.tableList);
              const selectGroups = this.currentSelectList.filter(
                (item) => !tableList.map((v) => v.id.toString()).includes(item.id.toString())
              );
              this.currentSelectList = [...selectGroups, ...payload];
              await this.fetchCustomTotal();
            }
          }
        };
        return typeMap[type]();
      },

      handlerAllChange (selection) {
        this.fetchSelectedGroups('all', selection);
      },

      handlerChange (selection, row) {
        this.fetchSelectedGroups('multiple', selection, row);
      },

      handleDropdownShow () {
        this.isDropdownShow = true;
        this.$refs.copyCascade.$refs.cascadeDropdown.hideHandler();
      },

      handleDropdownHide () {
        this.isDropdownShow = false;
      },

      handleCascadeEnter () {
        this.$nextTick(() => {
          this.isMouseCascadeEnter = true;
          const copyCascade = this.$refs.copyCascade;
          copyCascade && copyCascade.$refs.cascadeDropdown.showHandler();
        });
      },

      handleBatchProcess (type) {
        const typeMap = {
          remove: () => {
            if (!this.isNoBatchDelete()) {
              this.curMember = {};
              this.handleBatchDelete();
            }
          },
          renewal: () => {
            if (!this.isNoBatchRenewal()) {
              this.isShowRenewalDialog = true;
              this.curData = {};
            }
          }
        };
        return typeMap[type]();
      },

      async handleTriggerCopy (event, payload) {
        if (payload.id) {
          this.curCopyCascade = Object.assign({}, payload);
        }
        // 需先保存currentTarget，因为此方法为异步方法，同步代码执行完成后，浏览器会将event事件对象的currentTarget值重置为空
        const currentTarget = event.currentTarget;
        const params = {
          id: this.id,
          offset: 0,
          limit: 1000
        };
        const childTypeMap = {
          'user-selected': () => {
            this.handleResetCascade();
            if (!this.currentSelectList.length) {
              this.messageWarn(this.$t(`m.verify['请选择用户或组织成员']`), 3000);
              return;
            }
            const copyUserList = this.currentSelectList.filter(
              (item) => item.type === 'user'
            );
            if (!copyUserList.length) {
              this.messageWarn(this.$t(`m.verify['请选择用户']`), 3000);
              return;
            }
            const copyValue = copyUserList
              .map(
                (v) =>
                  `{${v.id}}${v.name}&full_name=${
                    v.user_departments && v.user_departments.length
                      ? v.user_departments
                      : ''
                  }&type=${v.type}*`
              )
              .join('\n');
            this.formatCopyValue(copyValue, event, currentTarget);
          },
          'userAndOrg-selected': () => {
            this.handleResetCascade();
            if (!this.currentSelectList.length) {
              this.messageWarn(this.$t(`m.verify['请选择用户或组织成员']`), 3000);
              return;
            }
            const copyValue = this.currentSelectList
              .map((v) =>
                v.type === 'user'
                  ? `{${v.id}}${v.name}&full_name=${
                    v.user_departments && v.user_departments.length
                      ? v.user_departments
                      : ''
                  }&type=${v.type}*`
                  : this.enableOrganizationCount
                    ? `{${v.id}}${v.name}&full_name=${v.full_name}&count=${v.member_count}&type=${v.type}*`
                    : `{${v.id}}${v.name}&full_name=${v.full_name}&type=${v.type}*`
              )
              .join('\n');
            this.formatCopyValue(copyValue, event, currentTarget);
          },
          'user-all': async () => {
            this.handleResetCascade();
            let copyUrl = this.copyUrl;
            if (this.curModeMap[this.routeMode]) {
              copyUrl = this.curModeMap[this.routeMode].copy.url;
            }
            const { data } = await this.$store.dispatch(
              copyUrl,
              params
            );
            if (data && data.results && data.results.length) {
              const copyUserList = data.results.filter((item) => item.type === 'user');
              if (!copyUserList.length) {
                this.messageWarn(this.$t(`m.verify['暂无可复制用户']`), 3000);
              } else {
                const copyValue = copyUserList
                  .map(
                    (v) =>
                      `{${v.id}}${v.name}&full_name=${
                        v.user_departments && v.user_departments.length
                          ? v.user_departments
                          : ''
                      }&type=${v.type}*`
                  )
                  .join('\n');
                this.formatCopyValue(copyValue, event, currentTarget);
              }
            } else {
              this.messageWarn(this.$t(`m.common['暂无可复制内容']`), 3000);
            }
          },
          'userAndOrg-all': async () => {
            this.handleResetCascade();
            let copyUrl = this.copyUrl;
            if (this.curModeMap[this.routeMode]) {
              copyUrl = this.curModeMap[this.routeMode].copy.url;
            }
            const { data } = await this.$store.dispatch(
              copyUrl,
              params
            );
            if (data && data.results && data.results.length) {
              const copyValue = data.results
                .map((v) =>
                  v.type === 'user'
                    ? `{${v.id}}${v.name}&full_name=${
                      v.user_departments && v.user_departments.length
                        ? v.user_departments
                        : ''
                    }&type=${v.type}*`
                    : this.enableOrganizationCount
                      ? `{${v.id}}${v.name}&full_name=${v.full_name}&count=${v.member_count}&type=${v.type}*`
                      : `{${v.id}}${v.name}&full_name=${v.full_name}&type=${v.type}*`
                )
                .join('\n');
              this.formatCopyValue(copyValue, event, currentTarget);
            } else {
              this.messageWarn(this.$t(`m.common['暂无可复制内容']`), 3000);
            }
          }
        };
        if (this.curCopyCascade.id) {
          return childTypeMap[this.curCopyCascade.id]
            ? childTypeMap[this.curCopyCascade.id]()
            : '';
        }
      },

      // 处理不同操作的复制
      formatCopyValue (payload, event, currentTarget) {
        const clipboard = new ClipboardJS(event.target, {
          text: () => payload
        });
        clipboard.on('success', () => {
          this.messageSuccess(
            this.$t(`m.info['已经复制到粘贴板，可在其他用户组添加成员时粘贴到手动输入框']`),
            3000,
            2
          );
        });
        clipboard.on('error', (e) => {
          console.error('复制失败', e);
        });
        clipboard.onClick({ currentTarget });
        // 调用后销毁，避免多次执行
        if (clipboard) {
          clipboard.destroy();
        }
        this.handleResetCascade();
      },

      // 重置级联数据
      handleResetCascade () {
        this.$nextTick(() => {
          this.copyValue = [];
        // if (this.$refs.copyCascade) {
        //   this.$refs.copyCascade.value = [];
        // }
        });
      },

      async handleEmptyClear () {
        this.handleEmptyRefresh();
      },

      async handleEmptyRefresh () {
        this.keyword = '';
        this.emptyData.tipType = '';
        this.groupTabList.forEach((item) => {
          if (this[item.empty]) {
            this[item.empty].tipType = '';
          }
        });
        this.resetPagination();
        await this.fetchInitData();
      },

      handleShowRenewal (payload) {
        this.isShowRenewalDialog = true;
        const params = _.cloneDeep(payload);
        if ((!['memberTemplate'].includes(this.routeMode) && ['memberTemplate'].includes(this.tabActive))) {
          this.$set(params, 'type', 'template');
        }
        this.curData = Object.assign({}, params);
      },

      handleAddMember () {
        this.isShowAddMemberDialog = true;
      },

      handleCancelAdd () {
        this.isShowAddMemberDialog = false;
      },

      handleAddAfterClose () {},

      async handleSubmitAdd (payload) {
        const externalPayload = _.cloneDeep(payload);
        this.loading = true;
        const { users, departments, templates, expiredAt } = payload;
        let expired = payload.policy_expired_at;
        // 4102444800：非永久时需加上当前时间
        if (expiredAt !== 4102444800) {
          const nowTimestamp = +new Date() / 1000;
          const tempArr = String(nowTimestamp).split('');
          const dotIndex = tempArr.findIndex((item) => item === '.');
          const nowSecond = parseInt(tempArr.splice(0, dotIndex).join(''), 10);
          expired = expired + nowSecond;
        }
        const arr = [];
        if (departments.length > 0) {
          arr.push(
            ...departments.map((item) => {
              return {
                id: item.id,
                type: 'department'
              };
            })
          );
        }
        if (users.length > 0) {
          arr.push(
            ...users.map((item) => {
              return {
                id: item.username,
                type: 'user'
              };
            })
          );
        }
        if (templates && templates.length) {
          arr.push(
            ...templates.map((item) => {
              return {
                id: item.id,
                type: 'template'
              };
            })
          );
        }
        const params = {
          members: arr,
          id: this.id
        };
        if (this.showExpiredAt) {
          params.expired_at = expired;
        }
        let url = 'userGroup/addUserGroupMember';
        if (this.curModeMap[this.routeMode]) {
          url = this.curModeMap[this.routeMode].addMember.url;
          params.subjects = _.cloneDeep(arr);
          delete params.members;
        }
        try {
          const { code, data } = await this.$store.dispatch(
            url,
            params
          );
          if (code === 0 && data) {
            if (this.externalRoutes.includes(this.$route.name)) {
              window.parent.postMessage(
                {
                  type: 'IAM',
                  data: externalPayload,
                  code: ['memberTemplate'].includes(this.tabActive) ? 'add_template_confirm' : 'add_user_confirm'
                },
                '*'
              );
            }
            this.isShowAddMemberDialog = false;
            this.messageSuccess(this.$t(`m.info['添加成员成功']`), 3000);
            this.fetchMemberList();
          }
        } catch (e) {
          console.error(e);
          this.messageAdvancedError(e);
        } finally {
          this.loading = false;
        }
      },

      handleBatchDelete () {
        if (this.currentSelectList.length === 1) {
          const payload = this.currentSelectList[0];
          if (this.curModeMap[this.curRouteMode]) {
            this.deleteDialog.subTitle = `${this.$t(`m.common['移除']`)}${this.$t(
              `m.common['【']`
            )}${payload.id}(${payload.name})${this.$t(`m.common['】']`)}${this.$t(
              `m.common['，']`
            )}${this.$t(`m.info['该用户/组织可能会失去关联用户组的权限']`)}${this.$t(`m.common['。']`)}`;
          } else {
            this.deleteDialog.subTitle = `${this.$t(`m.common['移除']`)}${this.$t(
              `m.common['【']`
            )}${payload.id}(${payload.name})${this.$t(`m.common['】']`)}${this.$t(
              `m.common['，']`
            )}${this.$t(`m.info['该成员将不再继承该组的权限']`)}${this.$t(`m.common['。']`)}`;
          }
        } else {
          if (this.curModeMap[this.curRouteMode]) {
            this.deleteDialog.subTitle = `${this.$t(`m.common['移除']`)} ${
              this.currentSelectList.length
            } ${this.$t(`m.common['个人员模板']`)}${this.$t(`m.common['，']`)}${this.$t(
              `m.info['相关人员将不再关联该用户组的权限']`
            )}${this.$t(`m.common['。']`)}`;
          } else {
            this.deleteDialog.subTitle = `${this.$t(`m.common['移除']`)} ${
              this.currentSelectList.length
            } ${this.$t(`m.common['位成员']`)}${this.$t(`m.common['，']`)}${this.$t(
              `m.info['这些成员将不再继承该组的权限']`
            )}${this.$t(`m.common['。']`)}`;
          }
        }
        this.deleteDialog.visible = true;
      },

      handleDelete (payload) {
        if (this.curModeMap[this.curRouteMode]) {
          this.deleteDialog.subTitle = `${this.$t(`m.common['移除']`)}${this.$t(
            `m.common['【']`
          )}${payload.id}(${payload.name})${this.$t(`m.common['】']`)}${this.$t(
            `m.common['，']`
          )}${this.$t(`m.info['该用户/组织可能会失去关联用户组的权限']`)}${this.$t(`m.common['。']`)}`;
          this.deleteDialog.visible = true;
          this.curMember = Object.assign(
            {},
            {
              id: payload.id,
              type: ['memberTemplate'].includes(this.routeMode) ? payload.type : 'template'
            }
          );
        } else {
          this.deleteDialog.subTitle = `${this.$t(`m.common['移除']`)}${this.$t(
            `m.common['【']`
          )}${payload.id}(${payload.name})${this.$t(`m.common['】']`)}${this.$t(
            `m.common['，']`
          )}${this.$t(`m.info['该成员将不再继承该组的权限']`)}${this.$t(`m.common['。']`)}`;
          this.deleteDialog.visible = true;
          this.curMember = Object.assign(
            {},
            {
              id: payload.id,
              type: payload.type
            }
          );
        }
      },

      handlePageChange (current) {
        const tabMap = {
          userOrgPerm: () => {
            this.userOrOrgPagination = Object.assign(this.userOrOrgPagination, { current });
            this.fetchUserOrOrgList();
          },
          memberTemplate: () => {
            this.memberPagination = Object.assign(this.memberPagination, { current });
            this.fetchMemberTemplateList();
          }
        };
        return tabMap[this.tabActive]();
      },

      handleLimitChange (limit) {
        const tabMap = {
          userOrgPerm: () => {
            this.userOrOrgPagination = Object.assign(this.userOrOrgPagination, { current: 1, limit });
            this.fetchUserOrOrgList();
          },
          memberTemplate: () => {
            this.memberPagination = Object.assign(this.memberPagination, { current: 1, limit });
            this.fetchMemberTemplateList();
          }
        };
        return tabMap[this.tabActive]();
      },

      handleAfterDeleteLeave () {
        this.deleteDialog.subTitle = '';
        this.curMember = {};
      },

      hideCancelDelete () {
        this.deleteDialog.visible = false;
      },

      async handleSubmitDelete () {
        this.deleteDialog.loading = true;
        try {
          let url = 'userGroup/deleteUserGroupMember';
          const params = {
            id: this.id,
            members: this.curMember.id
              ? [this.curMember]
              : this.currentSelectList.map(({ id, type }) => ({ id, type }))
          };
          let totalCount = params.members.length;
          if (this.curModeMap[this.routeMode]) {
            url = this.curModeMap[this.routeMode].removeMember.url;
            params.subjects = _.cloneDeep(params.members);
            totalCount = params.subjects.length;
            delete params.members;
          }
          const { code, data } = await this.$store.dispatch(
            url,
            params
          );
          if (code === 0 && data) {
            const externalParams = {
              ...params,
              count: totalCount
            };
            if (this.externalRoutes.includes(this.$route.name)) {
              window.parent.postMessage(
                {
                  type: 'IAM',
                  data: externalParams,
                  code: ['memberTemplate'].includes(this.tabActive) ? 'remove_template_confirm' : 'remove_user_confirm'
                },
                '*'
              );
            }
            this.messageSuccess(this.$t(`m.info['移除成功']`), 3000);
            this.handleRefreshTab();
            this.fetchMemberListCount();
            // 用户/组织模块在模板详情里移除成员需要同步更新加入人员模板的用户组列表数据
            if (['userOrgPerm'].includes(this.$route.name)) {
              bus.$emit('on-refresh-template-table', this.curDetailData);
            }
          }
        } catch (e) {
          console.error(e);
          this.messageAdvancedError(e);
        } finally {
          this.deleteDialog.loading = false;
          this.deleteDialog.visible = false;
        }
      },

      async handleRenewalSubmit (payload) {
        this.renewalLoading = true;
        const params = {
          groupId: this.id
        };
        if (Object.keys(this.curData).length) {
          const { id, type } = this.curData;
          this.$set(params, 'members', [{ expired_at: payload, id, type }]);
        } else {
          this.$set(params, 'members', payload);
        }
        try {
          await this.$store.dispatch('renewal/groupMemberPermRenewal', params);
          this.messageSuccess(this.$t(`m.renewal['续期成功']`), 3000);
          this.isShowRenewalDialog = false;
          this.$refs.groupMemberRef && this.$refs.groupMemberRef.clearSelection();
          if (this.externalRoutes.includes(this.$route.name)) {
            const externalParams = {
              ...params,
              count: params.members.length,
              id: this.id
            };
            delete externalParams.groupId;
            window.parent.postMessage(
              {
                type: 'IAM',
                data: externalParams,
                code: ['memberTemplate'].includes(this.tabActive) ? 'renewal_template_confirm' : 'renewal_user_confirm'
              },
              '*'
            );
          }
          this.handleRefreshTab();
        } catch (e) {
          console.error(e);
          this.messageAdvancedError(e);
        } finally {
          this.renewalLoading = false;
        }
      },

      async fetchMemberListCount () {
        // 搜索移除成员后，再去查询当前搜索的数据是不是最后一条
        if (
          (['userOrgPerm'].includes(this.tabActive) && !this.routeMode)
          && this.getGroupAttributes
          && this.getGroupAttributes().source_from_role
          && this.keyword) {
          const selectParams = {
            id: this.id,
            offset: 0,
            limit: 10
          };
          try {
            const { data } = await this.$store.dispatch('userGroup/getUserGroupMemberList', selectParams);
            this.userOrOrgCount = data.count || 0;
          } catch (e) {
            this.messageAdvancedError(e);
          }
        }
      },

      resetPagination () {
        this.userOrOrgPagination = Object.assign(this.userOrOrgPagination, {
          current: 1,
          limit: 10
        });
        this.memberPagination = Object.assign(this.memberPagination, {
          current: 1,
          limit: 10
        });
      }
    }
  };
</script>
<style lang="postcss">
.copy-user-group-cls {
  width: auto !important;
  .bk-cascade-options {
    width: auto !important;
    height: 72px !important;
  }
  .bk-cascade-panel {
    .bk-cascade-panel-ul {
      width: 100px !important;
    }
    .bk-cascade-panel {
      .bk-cascade-panel-ul {
        width: 110px !important;
      }
    }
  }
  &-lang {
    .bk-cascade-panel {
      .bk-cascade-panel-ul {
        width: 140px !important;
      }
      .bk-cascade-panel {
        .bk-cascade-panel-ul {
          width: 240px !important;
        }
      }
    }
  }
}
</style>

<style lang="postcss" scoped>
@import '@/css/mixins/member-table.css';
/deep/ .iam-table-cell-depart-cls {
  .cell {
    padding: 5px 0;
    padding-left: 15px;
    .user_departs {
      margin-bottom: 10px;
      word-break: break-all;
      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}

.group-member-button {
  &-item {
    &:not(&:last-child) {
      margin-right: 10px;
    }
    .group-dropdown-trigger-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      border: 1px solid #c4c6cc;
      height: 32px;
      min-width: 68px;
      border-radius: 2px;
      padding-left: 10px;
      padding-right: 5px;
      color: #63656e;
      &:hover {
        cursor: pointer;
        border-color: #979ba5;
      }
      .group-dropdown-text {
        font-size: 14px;
      }
      .bk-icon {
        font-size: 22px;
      }
    }
  }
}

/deep/ .bk-dropdown-menu {
  .bk-dropdown-content {
    padding-top: 0;
    cursor: pointer;
  }
  &.disabled,
  &.disabled *,
  .remove-disabled,
  .renewal-disabled {
    background-color: #fff !important;
    border-color: #dcdee5 !important;
    color: #c4c6cc !important;
    cursor: not-allowed;
  }
}

/deep/ .bk-cascade {
  font-size: 14px;
  &.is-default-trigger.is-unselected:before {
    color: #63656e;
  }
  &.is-disabled {
    background-color: #fff;
    border-color: #dcdee5;
    color: #c4c6cc;
    &.is-default-trigger.is-unselected:before,
    .bk-cascade-angle {
      color: #c4c6cc;
    }
  }
}

/deep/ .group-member-wrapper {
  .group-tab-wrapper {
    margin-top: 16px;
    .bk-tab-section {
      display: none;
    }
    .panel-count {
      min-width: 16px;
      height: 16px;
      line-height: 16px;
      padding: 0 8px;
      border-radius: 8px;
      text-align: center;
      font-size: 12px;
      color: #979ba5;
      background-color: #f0f1f5;
      &-active {
        background-color: #e1ecff;
        color: #3a84ff;
      }
    }
  }
}

/deep/ .custom-expired-header-cell {
  color: inherit;
  text-decoration: underline;
  text-decoration-style: dashed;
  text-underline-position: under;
  cursor: pointer;
}
</style>
