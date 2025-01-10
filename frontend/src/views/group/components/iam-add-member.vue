<template>
  <div>
    <bk-dialog
      v-model="isShowDialog"
      width="960"
      title=""
      :mask-close="false"
      :close-icon="false"
      draggable
      header-position="left"
      ext-cls="iam-add-member-dialog"
      @after-leave="handleAfterLeave"
    >
      <!-- eslint-disable max-len -->
      <div slot="header" class="title">
        <template v-if="showExpiredAt">
          <div v-if="isBatch">{{ $t(`m.common['批量添加成员']`) }}</div>
          <div v-else>
            <div v-if="isPrev">
              {{ $t(`m.common['添加成员至']`) }}
              {{ $t(`m.common['【']`) }}<span class="member-title" :title="name">{{ name }}</span
              >{{ $t(`m.common['】']`) }}
            </div>
            <div
              v-else
              :title="
                $t(`m.common['设置新用户加入用户组的有效期']`, {
                  value: `${$t(`m.common['【']`)}${name}${$t(`m.common['】']`)}`
                })
              "
            >
              <!-- {{ $t(`m.common['设置新用户加入']`) }}<span class="expired-at-title" :title="name">{{$t(`m.common['【']`)}}{{ name }}</span>{{$t(`m.common['】']`)}}{{ $t(`m.common['用户组的有效期']`) }} -->
              {{
                $t(`m.common['设置新用户加入用户组的有效期']`, {
                  value: `${$t(`m.common['【']`)}${name}${$t(`m.common['】']`)}`
                })
              }}
            </div>
          </div>
        </template>
        <template v-else>
          <template v-if="title !== ''">
            {{ title }}
          </template>
          <template v-else>
            {{ $t(`m.common['选择用户或组织']`) }}
          </template>
        </template>
      </div>
      <div class="add-member-content-wrapper" v-bkloading="{ isLoading, opacity: 1 }" :style="style">
        <div v-show="!isLoading">
          <template v-if="isPrev">
            <div class="left">
              <div class="tab-wrapper">
                <section
                  v-for="(item, index) in panels"
                  :key="item.name"
                  :class="[
                    'tab-item',
                    { 'has-margin-left': index !== 0 },
                    { 'tab-item-active': tabActive === item.name }
                  ]"
                  @click.stop="handleTabChange(item)"
                >
                  {{ item.label }}
                </section>
              </div>
              <!-- 所有平台都开放搜索，通过选中做校验 -->
              <div
                :class="['search-input', { active: isSearchFocus }, { disabled: isAll && !isAllFlag }]"
                v-if="isOrganization"
              >
                <bk-dropdown-menu align="left" ref="dropdown" trigger="click">
                  <template slot="dropdown-trigger">
                    <Icon
                      class="search-icon"
                      :type="searchConditionValue === 'fuzzy' ? 'fuzzy-search-allow' : 'exact-search-allow'"
                    />
                  </template>
                  <ul class="bk-dropdown-list" slot="dropdown-content">
                    <li v-for="item in searchConditionList" :key="item.id" @click.stop="handleConditionSelcted(item)">
                      <a href="javascript:;" :class="{ active: item.id === searchConditionValue }">
                        <Icon
                          class="search-config-icon"
                          style="font-size: 16px"
                          :type="item.id === 'fuzzy' ? 'fuzzy-search-allow' : 'exact-search-allow'"
                        />
                        {{ item.name }}
                      </a>
                    </li>
                  </ul>
                </bk-dropdown-menu>
                <bk-input
                  v-model="keyword"
                  :placeholder="$t(`m.common['搜索提示1']`)"
                  maxlength="64"
                  clearable
                  :disabled="isAll && !isAllFlag"
                  ext-cls="iam-add-member-search-input-cls"
                  @focus="handleSearchInput"
                  @blur="handleSearchBlur"
                  @keyup.enter.native="handleSearch"
                  @keyup.up.native="handleKeyup"
                  @keyup.down.native="handleKeydown"
                />
              </div>
              <div class="member-tree-wrapper" v-bkloading="{ isLoading: treeLoading, opacity: 1 }" v-if="isOrganization">
                <template v-if="isShowMemberTree">
                  <div class="tree">
                    <infinite-tree
                      ref="memberTreeRef"
                      :all-data="treeList"
                      style="height: 400px"
                      :is-rating-manager="curIsRatingManager"
                      :key="infiniteTreeKey"
                      :is-disabled="isAll"
                      :empty-data="emptyData"
                      :has-selected-users="formatAllSelectedUsers"
                      :has-selected-departments="formatAllSelectedDeparts"
                      @async-load-nodes="handleRemoteLoadNode"
                      @expand-node="handleExpanded"
                      @on-select="handleOnSelected"
                      @on-show-limit="handleShowLimitDialog"
                      @on-clear="handleEmptyClear"
                      @on-refresh="handleEmptyRefresh"
                    />
                  </div>
                </template>
                <template v-if="isShowSearchResult">
                  <div class="search-content">
                    <template v-if="isHasSearchResult">
                      <dialog-infinite-list
                        ref="searchedResultsRef"
                        style="height: 400px"
                        :all-data="searchedResult"
                        :focus-index.sync="focusItemIndex"
                        :is-disabled="isAll"
                        :has-selected-users="formatAllSelectedUsers"
                        :has-selected-departments="formatAllSelectedDeparts"
                        @on-checked="handleSearchResultSelected"
                        @on-show-limit="handleShowLimitDialog"
                      >
                      </dialog-infinite-list>
                    </template>
                    <template v-if="isSearchResultTooMuch">
                      <div class="too-much-wrapper">
                        <Icon type="warning" class="much-tips-icon" />
                        <p class="text">{{ $t(`m.info['搜索结果']`) }}</p>
                      </div>
                    </template>
                    <template v-if="isSearchResultEmpty">
                      <div class="search-empty-wrapper">
                        <ExceptionEmpty
                          :type="emptyData.type"
                          :empty-text="emptyData.text"
                          :tip-text="emptyData.tip"
                          :tip-type="emptyData.tipType"
                          @on-clear="handleEmptyClear"
                          @on-refresh="handleEmptyRefresh"
                        />
                      </div>
                    </template>
                  </div>
                </template>
              </div>
              <div v-if="isManual">
                <div class="manual-input-alert">
                  <bk-alert
                    type="info"
                    :title="$t(`m.userGroupDetail['单次最多添加100个成员/组织，批量复制的内容不可随意编辑，如超过上限100个，可通过再次批量粘贴添加人员']`)"
                  />
                </div>
                <div class="manual-wrapper">
                  <div class="manual-wrapper-left">
                    <bk-input
                      ref="manualInputRef"
                      type="textarea"
                      class="manual-textarea"
                      v-model="manualValue"
                      :placeholder="$t(`m.common['手动输入提示']`)"
                      :rows="14"
                      :disabled="isAll"
                      @input="handleManualInput"
                    />
                    <p class="manual-error-text" v-if="isManualInputOverLimit">{{ $t(`m.common['手动输入提示1']`) }}</p>
                    <p class="manual-error-text pr10" v-if="manualInputError">
                      {{ $t(`m.common['手动输入提示2']`) }}
                      <template v-if="isShowScopeEntry">
                        {{ $t(`m.common['，']`) }}{{ $t(`m.common['请尝试']`)
                        }}<span class="highlight" @click="handleSkip">{{ $t(`m.common['修改授权人员范围']`) }}</span>
                      </template>
                    </p>
                    <div class="manual-bottom-btn">
                      <bk-button
                        theme="primary"
                        :outline="true"
                        style="width: 168px"
                        :loading="manualAddLoading"
                        :disabled="isManualDisabled || isAll"
                        @click="handleAddManualUser"
                      >
                        {{ $t(`m.common['解析并添加']`) }}
                      </bk-button>
                      <bk-button style="margin-left: 10px" @click="handleClearManualUser">
                        {{ $t(`m.common['清空']`) }}
                      </bk-button>
                    </div>
                  </div>
                  <div class="manual-wrapper-right">
                    <bk-input
                      v-model="tableKeyWord"
                      class="manual-input-wrapper"
                      :placeholder="$t(`m.common['搜索解析结果']`)"
                      :right-icon="'bk-icon icon-search'"
                      :clearable="true"
                      @clear="handleClearSearch"
                      @enter="handleTableSearch"
                      @right-icon-click="handleTableSearch"
                    />
                    <div>
                      <bk-table
                        ref="manualTableRef"
                        size="small"
                        :data="manualTableList"
                        :max-height="340"
                        :ext-cls="'manual-table-wrapper'"
                        :outer-border="false"
                        :header-border="false"
                        @select="handleSelectChange"
                        @select-all="handleSelectAllChange"
                      >
                        <bk-table-column type="selection" align="center" :selectable="getDefaultSelect" />
                        <bk-table-column :label="$t(`m.common['用户名']`)" prop="name">
                          <template slot-scope="{ row }">
                            <span :title="formatUserName(row)">
                              {{ formatUserName(row) }}
                            </span>
                          </template>
                        </bk-table-column>
                        <template slot="empty">
                          <ExceptionEmpty
                            :type="emptyTableData.type"
                            :empty-text="emptyTableData.text"
                            :tip-text="emptyTableData.tip"
                            :tip-type="emptyTableData.tipType"
                            @on-clear="handleClearSearch"
                          />
                        </template>
                      </bk-table>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="isMemberTemplate" class="template-wrapper">
                <IamMemberTemplateTable
                  ref="memberTableRef"
                  :group-id="curId"
                  :default-temp-id-list="defaultTempIdList"
                  :has-selected-templates="hasSelectedTemplates"
                  @on-selected-templates="handleSelectedTemplates"
                />
              </div>
            </div>
            <div class="right">
              <div class="result-preview">
                <div>{{ $t(`m.common['结果预览']`) }}</div>
                <bk-button
                  size="small"
                  theme="primary"
                  text
                  :disabled="!isShowSelectedText || isAll"
                  @click="handleDeleteAll"
                >
                  {{ $t(`m.common['清空']`) }}
                </bk-button>
              </div>
              <div class="header">
                <div class="has-selected">
                  <template v-if="curLanguageIsCn">
                    <template v-if="isShowSelectedText">
                      {{ $t(`m.common['已选择']`) }}
                      <template v-if="hasSelectedDepartments.length">
                        <span class="organization-count">{{ hasSelectedDepartments.length }}</span>
                        {{ $t(`m.common['个']`) }}{{ $t(`m.common['组织']`) }}
                      </template>
                      <span v-if="isShowComma">{{ $t(`m.common['，']`) }}</span>
                      <template v-if="hasSelectedUsers.length > 0">
                        <span class="user-count">{{ hasSelectedUsers.length }}</span>
                        {{ $t(`m.common['个']`) }}{{ $t(`m.common['用户']`) }}
                      </template>
                      <template v-if="isExistMemberTemplate && hasSelectedTemplates.length > 0">
                        <span v-if="hasSelectedUsers.length > 0">{{ $t(`m.common['，']`) }}</span>
                        <span class="template-count">{{ hasSelectedTemplates.length }}</span>
                        {{ $t(`m.common['个']`) }}{{ $t(`m.memberTemplate['人员模板']`) }}
                      </template>
                    </template>
                  <!-- <template v-else>
                    <span class="user-count">0</span>
                  </template> -->
                  </template>
                  <template v-else>
                    <template v-if="isShowSelectedText">
                      <span class="organization-count">{{ hasSelectedDepartments.length }}</span>
                      <span>Org</span>
                      <span v-if="isShowComma">{{ $t(`m.common['，']`) }}</span>
                      <template v-if="hasSelectedUsers.length > 0">
                        <span class="user-count">{{ hasSelectedUsers.length }}</span>
                        <span>User</span>
                      </template>
                      <template v-if="isExistMemberTemplate && hasSelectedTemplates.length > 0">
                        <span v-if="hasSelectedUsers.length > 0">{{ $t(`m.common['，']`) }}</span>
                        <span class="template-count">{{ hasSelectedTemplates.length }}</span>
                        <span>Member template</span>
                      </template>
                    </template>
                    {{ $t(`m.common['已选择']`) }}
                  </template>
                </div>
              </div>
              <div class="content">
                <div class="organization-content" v-if="isDepartSelectedEmpty">
                  <div class="organization-item" v-for="item in hasSelectedDepartments" :key="item.id">
                    <div class="organization-item-left">
                      <Icon type="file-close" class="folder-icon" />
                      <span
                        :class="[
                          'organization-name'
                        ]"
                        :title="nameType(item)"
                      >
                        {{ item.name }}
                      </span>
                      <span
                        v-if="item.showCount && enableOrganizationCount"
                        class="user-count"
                      >
                        {{ `(${item.count})` }}
                      </span>
                    </div>
                    <Icon bk type="close" class="delete-depart-icon" @click="handleDelete(item, 'organization')" />
                  </div>
                </div>
                <div class="user-content" v-if="isUserSelectedEmpty">
                  <div
                    :class="[
                      'user-item',
                      { 'user-item-bottom': isTempSelectedEmpty }
                    ]"
                    v-for="item in hasSelectedUsers"
                    :key="item.id"
                  >
                    <div class="user-item-left">
                      <Icon type="personal-user" class="user-icon" />
                      <span class="user-name" :title="nameType(item)"
                      >{{ item.username }}<template v-if="item.name !== ''">({{ item.name }})</template>
                      </span>
                    </div>
                    <Icon bk type="close" class="delete-icon" @click="handleDelete(item, 'user')" />
                  </div>
                </div>
                <div class="template-content" v-if="isTempSelectedEmpty">
                  <div
                    class="template-item"
                    v-for="item in hasSelectedTemplates"
                    :key="item.id">
                    <div class="template-item-left">
                      <Icon type="renyuanmuban" class="user-icon" />
                      <span class="template-name" :title="nameType(item)">
                        {{ item.name }}
                      </span>
                    </div>
                    <Icon bk type="close" class="delete-icon" @click="handleDelete(item, 'template')" />
                  </div>
                </div>
                <div class="selected-empty-wrapper" v-if="isSelectedEmpty">
                  <ExceptionEmpty />
                </div>
              </div>
            </div>
          </template>
          <template v-else>
            <div class="set-user-deadline">
              <iam-deadline :value="expiredAt" type="dialog" @on-change="handleDeadlineChange" />
            </div>
          </template>
        </div>
      </div>
      <div slot="footer">
        <div v-if="showLimit" class="limit-wrapper">
          <bk-checkbox :true-value="true" :false-value="false" v-model="isAll">
            {{ $t(`m.common['全员']`) }}
          </bk-checkbox>
        </div>
        <template v-if="showExpiredAt">
          <template v-if="isPrev">
            <bk-button theme="primary" :disabled="isDisabled" @click="handleNextStep">
              {{ $t(`m.common['下一步']`) }}
            </bk-button>
          </template>
          <template v-else>
            <bk-button @click="handlePrevStep">{{ $t(`m.common['上一步']`) }}</bk-button>
            <bk-button
              style="margin-left: 10px"
              theme="primary"
              :disabled="isNextSureDisabled"
              :loading="loading"
              @click="handleSave"
            >
              {{ $t(`m.common['确定']`) }}
            </bk-button>
          </template>
        </template>
        <template v-else>
          <bk-button
            theme="primary"
            :disabled="isDisabled && !isAll"
            @click="handleSave"
          >
            {{ $t(`m.common['确定']`) }}
          </bk-button>
        </template>
        <bk-button style="margin-left: 10px" :disabled="loading" @click="handleCancel">
          {{ $t(`m.common['取消']`) }}
        </bk-button>
      </div>
    </bk-dialog>
    
    <!-- 蓝盾侧限制组织架构人员提示框 -->
    <IamLimitOrgDialog :show.sync="isShowLimitDialog" :title="limitOrgNodeTip" />
  </div>
</template>

<script>
  import _ from 'lodash';
  import InfiniteTree from '@/components/infinite-tree';
  import dialogInfiniteList from '@/components/dialog-infinite-list';
  import IamDeadline from '@/components/iam-deadline/horizontal';
  import IamMemberTemplateTable from '@/components/iam-member-template-table';
  import IamLimitOrgDialog from '@/components/iam-limit-org-dialog';
  import { guid, formatCodeData, existValue, getParamsValue } from '@/common/util';
  import { NO_VERIFY_ORG_ROUTES } from '@/common/constants';
  import { mapGetters } from 'vuex';

  // 去除()以及之间的字符
  const getUsername = (str) => {
    const array = str.split('');
    const index = array.findIndex((item) => ['(', ')'].includes(item));
    if (index !== -1) {
      return array.splice(0, index).join('');
    }
    return str;
  };

  export default {
    name: '',
    inject: {
      getGroupAttributes: { value: 'getGroupAttributes', default: null }
    },
    components: {
      InfiniteTree,
      dialogInfiniteList,
      IamDeadline,
      IamMemberTemplateTable,
      IamLimitOrgDialog
    },
    props: {
      show: {
        type: Boolean,
        default: false
      },
      users: {
        type: Array,
        default: () => []
      },
      departments: {
        type: Array,
        default: () => []
      },
      templates: {
        type: Array,
        default: () => []
      },
      // 已选择的是否需要禁用
      disabled: {
        type: Boolean,
        default: false
      },
      loading: {
        type: Boolean,
        default: false
      },
      showExpiredAt: {
        type: Boolean,
        default: false
      },
      name: {
        type: String,
        default: ''
      },
      id: {
        type: [String, Number],
        default: ''
      },
      title: {
        type: String,
        default: ''
      },
      isRatingManager: {
        type: Boolean,
        default: false
      },
      showLimit: {
        type: Boolean,
        default: false
      },
      allChecked: {
        type: Boolean,
        default: false
      },
      isBatch: {
        type: Boolean,
        default: false
      },
      routeMode: {
        type: String,
        default: ''
      }
    },
    data () {
      return {
        isShowDialog: false,
        isShowLimitDialog: false,
        limitOrgNodeTip: '',
        keyword: '',
        treeLoading: false,
        isBeingSearch: false,
        searchedUsers: [],
        searchedDepartment: [],
        hasSelectedUsers: [],
        hasSelectedDepartments: [],
        hasSelectedTemplates: [],
        treeList: [],
        infiniteTreeKey: -1,
        searchedResult: [],
        // 搜索时 键盘上下键 hover 的 index
        focusItemIndex: -1,
        isPrev: true,
        expiredAt: 15552000,
        requestQueue: ['categories', 'memberList'],
        defaultDepartments: [],
        defaultUsers: [],
        isShowTooMuch: false,
        searchConditionList: [
          {
            id: 'fuzzy',
            name: this.$t(`m.common['模糊搜索']`)
          },
          {
            id: 'exact',
            name: this.$t(`m.common['精确搜索']`)
          }
        ],
        searchConditionValue: 'fuzzy',
        isSearchFocus: false,

        panels: [
          { name: 'organization', label: this.$t(`m.common['组织架构']`) },
          { name: 'manual', label: this.$t(`m.common['手动输入']`) },
          { name: 'memberTemplate', label: this.$t(`m.memberTemplate['人员模板']`) }
        ],
        tabActive: 'organization',
        manualValue: '',
        manualAddLoading: false,
        manualInputError: false,
        manualValueBackup: [],
        manualOrgList: [],
        manualUserList: [],
        filterUserList: [],
        filterDepartList: [],
        usernameList: [],
        isAll: false,
        isAllFlag: false,
        externalSource: '',
        enableOrganizationCount: window.ENABLE_ORGANIZATION_COUNT.toLowerCase() === 'true',
        emptyData: {
          type: '',
          text: '',
          tip: '',
          tipType: ''
        },
        emptyTableData: {
          type: 'empty',
          text: '请先从左侧输入并解析',
          tip: '',
          tipType: ''
        },
        tableKeyWord: '',
        manualTableList: [],
        manualTableListStorage: [],
        hasSelectedManualDepartments: [],
        hasSelectedManualUsers: [],
        defaultTempIdList: [],
        curId: 0,
        needMemberTempRoutes: ['userGroup', 'userGroupDetail', 'createUserGroup', 'cloneUserGroup'],
        regValue: /，|,|；|;|、|\\|\n|\s/
      };
    },
    computed: {
      ...mapGetters(['user', 'externalSystemId', 'externalSystemsLayout']),
      isLoading () {
        return this.requestQueue.length > 0;
      },
      isDisabled () {
        return this.isLoading
         || (
          this.hasSelectedUsers.length < 1
          && this.hasSelectedDepartments.length < 1
          && this.hasSelectedTemplates.length < 1
          );
      },
      isNextSureDisabled () {
        return this.expiredAt === 0;
      },
      isHasSearchResult () {
        return (this.searchedDepartment.length > 0 || this.searchedUsers.length > 0) && !this.treeLoading;
      },
      isSearchResultTooMuch () {
        return !this.treeLoading && this.isShowTooMuch;
      },
      isSearchResultEmpty () {
        return (
          this.searchedDepartment.length < 1
          && this.searchedUsers.length < 1
          && !this.treeLoading
          && !this.isShowTooMuch
        );
      },
      isShowSelectedText () {
        return this.hasSelectedDepartments.length > 0
        || this.hasSelectedUsers.length > 0
        || this.hasSelectedTemplates.length > 0;
      },
      isShowSearchResult () {
        return this.isBeingSearch && !this.treeLoading;
      },
      isShowMemberTree () {
        return !this.isBeingSearch && !this.treeLoading;
      },
      isDepartSelectedEmpty () {
        return this.hasSelectedDepartments.length > 0;
      },
      isUserSelectedEmpty () {
        return this.hasSelectedUsers.length > 0;
      },
      isTempSelectedEmpty () {
        return this.hasSelectedTemplates.length > 0;
      },
      isSelectedEmpty () {
        return this.hasSelectedDepartments.length < 1
        && this.hasSelectedUsers.length < 1
         && this.hasSelectedTemplates.length < 1;
      },
      style () {
        if (this.showExpiredAt) {
          if (this.isPrev) {
            return {
              // height: this.curLanguageIsCn ? '383px' : '400px'
              height: this.curLanguageIsCn ? '510px' : '527px'
            };
          }
          return {
            height: '80px'
          };
        }
        return {
          // height: '383px'
          height: '510px'
        };
      },
      isOrganization () {
        return this.tabActive === 'organization';
      },
      isManual () {
        return this.tabActive === 'manual';
      },
      isMemberTemplate () {
        return ['memberTemplate'].includes(this.tabActive);
      },
      isManualInputOverLimit () {
        if (this.manualValue === '') {
          return false;
        }
        const MAX_LEN = 100;
        return this.manualValue.split(this.regValue).filter((item) => item !== '').length > MAX_LEN;
      },
      isManualDisabled () {
        return this.manualValue === '' || this.isManualInputOverLimit;
      },
      manualValueActual () {
        return this.manualValue.replace(/，|,|；|;|、|\\|\n|\s+/g, ';');
      },
      curIsRatingManager () {
        if (this.isAllFlag) {
          return false;
        }
        return this.isRatingManager;
      },
      isHierarchicalAdmin () {
        // const { navCurRoleId, curRoleId, roleList } = this.$store.getters;
        // const roleId = navCurRoleId || curRoleId;
        return this.user.role || {};
      },
      isShowScopeEntry () {
        return this.isHierarchicalAdmin.type === 'rating_manager' && !this.externalSystemsLayout.addMemberBoundary.hideScopeRangeEntry;
      },
      nameType () {
        return (payload) => {
          const { name, type, username, full_name: fullName } = payload;
          const typeMap = {
            user: () => {
              if (fullName) {
                const result = fullName.indexOf(';') > -1 ? fullName.replace(/[，,;；]/g, '\n') : fullName;
                return result;
              } else {
                return name ? `${username}(${name})` : username;
              }
            },
            depart: () => {
              return fullName || payload.fullName || name;
            },
            template: () => {
              return name;
            }
          };
          return typeMap[type] ? typeMap[type]() : typeMap['user']();
        };
      },
      formatUserName () {
        return (payload) => {
          return ['depart', 'department'].includes(payload.type) ? payload.name : `${payload.username}(${payload.name})`;
        };
      },
      formatAllSelectedUsers () {
       return [...this.hasSelectedUsers, ...this.hasSelectedManualUsers];
      },
      formatAllSelectedDeparts () {
       return [...this.hasSelectedDepartments, ...this.hasSelectedManualDepartments];
      },
      isStaff () {
        return this.user.role.type === 'staff';
      },
      isAdminGroup () {
        return this.getGroupAttributes && this.getGroupAttributes().source_from_role;
      },
      isShowMemberTemplate () {
        return this.needMemberTempRoutes.includes(this.$route.name) && !this.isStaff && !this.isAdminGroup;
      },
      isExternalApp () {
        return existValue('externalApp') && this.externalSystemId;
      },
      isExistMemberTemplate () {
        return this.isExternalApp ? this.isShowExternalMemberTemplate : this.isShowMemberTemplate;
      },
      // 蓝盾场景
      isShowExternalMemberTemplate () {
        return !['staff', 'rating_manager'].includes(this.user.role.type) && this.needMemberTempRoutes.includes(this.$route.name) && !this.isAdminGroup;
      },
      isShowComma () {
        return this.hasSelectedDepartments.length > 0
         && (this.hasSelectedUsers.length > 0 || (this.hasSelectedTemplates.length > 0 && this.isExistMemberTemplate));
      },
      // 不需要校验组织架构授权范围的页面模块
      isUnLimitedScope () {
        return getParamsValue('search_scene') === 'add' || NO_VERIFY_ORG_ROUTES.includes(this.$route.name);
      },
      // 蓝盾侧需要限制勾选部门的页面
      isDisabledOrgPage () {
        return this.isExternalApp && ['createUserGroup', 'userGroupDetail'].includes(this.$route.name);
      },
      // 蓝盾侧通过环境变量注入限制勾选的组织架构
      isLimitSelectNode () {
        return (payload) => {
          const disabledMembers = window.DEPARTMENT_IDS_NOT_ALLOWED_AS_GROUP_MEMBER;
          if (this.isDisabledOrgPage && disabledMembers.length > 0) {
            const { id, type, username } = payload;
            const keys = type === 'user' ? username : String(id);
            const result = disabledMembers.split(',').includes(keys);
            return result;
          }
          return false;
        };
      }
    },
    watch: {
      show: {
        handler (value) {
          this.isShowDialog = !!value;
          if (this.isShowDialog) {
            if (!this.isExistMemberTemplate) {
              this.panels = this.panels.filter((item) => !['memberTemplate'].includes(item.name));
            }
            this.curId = this.id;
            this.infiniteTreeKey = new Date().getTime();
            this.hasSelectedUsers.splice(0, this.hasSelectedUsers.length, ...this.users);
            this.hasSelectedDepartments.splice(0, this.hasSelectedDepartments.length, ...this.departments);
            this.hasSelectedTemplates.splice(0, this.hasSelectedDepartments.length, ...this.templates);
            this.fetchInitData();
          }
        },
        immediate: true
      },
      keyword (newVal, oldVal) {
        this.focusItemIndex = -1;
        if (!newVal && oldVal) {
          if (this.isBeingSearch) {
            this.infiniteTreeKey = new Date().getTime();
            this.isBeingSearch = false;
            if (this.isAllFlag || !this.isRatingManager) {
              this.fetchCategories(true, false);
              return;
            }
            this.fetchRoleSubjectScope(true, false);
          }
        }
      },
      allChecked: {
        handler (value) {
          this.isAll = !!value;
        },
        immediate: true
      },
      id: {
        handler (value) {
          this.curId = value;
        },
        immediate: true
      }
    },
    created () {
      const { name, query } = this.$route;
      if (name === 'gradingAdminCreate') {
        this.handleSave();
      }
      if (query.source && query.source === 'externalApp') {
        this.externalSource = query.source;
      }
    },
    methods: {
      getDefaultSelect () {
        const list = [...this.hasSelectedManualDepartments, this.hasSelectedManualUsers];
        return list.length > 0;
      },

      async fetchInitData () {
        if (this.showExpiredAt) {
          await this.fetchMemberList();
          if (this.isBatch) {
            await this.fetchCategoriesList();
          }
        } else {
          this.requestQueue = ['memberList'];
          this.fetchMemberList();
        }
      },

      fetchManualTableData () {
        this.$nextTick(() => {
          this.manualTableList.forEach((item) => {
            if (this.$refs.manualTableRef) {
              const hasSelectedUsers = [...this.hasSelectedUsers, ...this.hasSelectedManualUsers].map((v) => `${v.username}${v.name}`);
              const hasSelectedDepartments = [...this.hasSelectedDepartments, ...this.hasSelectedManualDepartments]
                .map((v) => String(v.id));
              this.$refs.manualTableRef.toggleRowSelection(
                item,
                (hasSelectedUsers.includes(`${item.username}${item.name}`))
                  || (['depart', 'department'].includes(item.type) && hasSelectedDepartments.includes(String(item.id)))
              );
            }
          });
        });
      },

      handleSearchInput () {
        this.isSearchFocus = true;
      },

      handleSearchBlur () {
        this.isSearchFocus = false;
      },

      handleEmptyRefresh () {
        this.fetchInitData();
        this.requestQueue = [];
      },

      handleEmptyClear () {
        this.keyword = '';
        this.emptyData.tipType = '';
        this.fetchInitData();
        this.requestQueue = [];
      },

      handleTabChange ({ name }) {
        this.tabActive = name;
        // 已选择的需要从输入框中去掉
        if (
          this.tabActive === 'manual'
          && (this.hasSelectedUsers.length > 0 || this.hasSelectedDepartments.length > 0)
          && this.manualValue !== ''
        ) {
          this.fetchRegOrgData();
          const templateArr = [];
          const usernameList = this.hasSelectedUsers.map((item) => item.username);
          const manualValueBackup = this.filterUserList.filter((item) => item !== '');
          manualValueBackup.forEach((item) => {
            const name = getUsername(item);
            if (!usernameList.includes(name)) {
              templateArr.push(item);
            }
          });
          // 处理切换tab后按原有的格式回显
          const hasSelectedData = this.manualValueActual
            .split(';')
            .filter((item) => templateArr.includes(item) || this.filterDepartList.includes(item));
          this.manualValue = hasSelectedData.join('\n');
        }
        this.fetchManualTableData();
      },

      handleManualInput (value) {
        this.manualOrgList = [];
        this.manualUserList = [];
        if (value) {
          const inputValue = _.cloneDeep(value.split()[0]);
          if (
            inputValue.indexOf('{') > -1
            && inputValue.indexOf('}') > -1
            && (inputValue.includes('&type=department') || inputValue.includes('&type=user'))
          ) {
            this.$nextTick(() => {
              this.manualValue = '';
              if (this.$refs.manualInputRef) {
                this.$refs.manualInputRef.curValue = '';
              }
            });
            const splitValue = value.split(/\n/).map((item) => {
              const str = item.slice(item.indexOf('{') + 1, item.indexOf('}'));
              if (item.indexOf('{') > -1 && item.indexOf('}') > -1) {
                if (item.includes('&type=user')) {
                  this.manualUserList.push(item);
                  item = item.substring(item.indexOf('{') + 1, item.indexOf('}'));
                }
                if (/^[+-]?\d*(\.\d*)?(e[+-]?\d+)?$/.test(str) && item.includes('type=department')) {
                  this.manualOrgList.push(item);
                  item = item.substring(item.indexOf('{'), item.indexOf('&') > -1 ? item.indexOf('&') : item.length);
                }
              }
              return item;
            });
            if (this.$refs.manualInputRef) {
              setTimeout(() => {
                this.manualValue = _.cloneDeep(splitValue.join('\n'));
                this.$refs.manualInputRef.curValue = _.cloneDeep(splitValue.join('\n'));
              }, 200);
            }
          }
        }
        this.manualInputError = false;
      },

      fetchRegOrgData () {
        const manualList = this.manualValueActual.split(this.regValue).filter((item) => item !== '');
        this.filterDepartList = manualList.filter((item) => {
          if (item.indexOf('{') > -1 && item.indexOf('}') > -1) {
            const str = item.slice(item.indexOf('{') + 1, item.indexOf('}'));
            if (/^[+-]?\d*(\.\d*)?(e[+-]?\d+)?$/.test(str)) {
              return item;
            }
          }
        });
        this.filterUserList = manualList.filter((item) => !this.filterDepartList.includes(item) && item !== '');
      },

      handleClearManualUser () {
        this.manualValue = '';
        this.manualInputError = false;
      },

      // 处理同步异步操作数据
      async formatSearchData (data, curData) {
        if (data) {
          const { users, departments } = data;
          if (users && users.length) {
            users.forEach((item) => {
              item.type = 'user';
            });
            const result = await this.fetchSubjectScopeCheck(users, 'user');
            if (result && result.length) {
              const hasSelectedUsers = [...this.hasSelectedUsers, ...this.hasSelectedManualUsers];
              const userTemp = result.filter((item) => {
                return !hasSelectedUsers.map((subItem) =>
                  `${subItem.username}&${subItem.name}`).includes(`${item.username}&${item.name}`);
              });
              this.hasSelectedUsers.push(...userTemp);
              this.hasSelectedManualUsers.push(...userTemp);
              // 保存原有格式
              let formatStr = _.cloneDeep(this.manualValue);
              const usernameList = result.map((item) => item.username);
              usernameList.forEach((item) => {
                // 处理既有部门又有用户且不连续相同类型的展示数据
                formatStr = formatStr
                  .replace(this.evil('/' + item + '(，|,|；|;|、|\\||\\n|\\s\\n|)/'), '')
                  .replace(/(\s*\r?\n\s*)+/g, '\n')
                  .replace(';;', '');
                // 处理复制全部用户不相连的两个不在授权范围内的用户存在空字符
                formatStr = formatStr
                  .split(this.regValue)
                  .filter((item) => item !== '' && item !== curData)
                  .join('\n');
              });
              // 处理只选择全部符合条件的用户，还存在特殊符号的情况
              if (formatStr === '\n' || formatStr === '\s' || formatStr === ';') {
                formatStr = '';
              }
              this.manualValue = _.cloneDeep(formatStr);
            }
          }
          if (departments && departments.length) {
            departments.forEach((item) => {
              item.type = 'depart';
              item.showCount = true;
              if (!item.hasOwnProperty('count')) {
                item.count = item.recursive_member_count;
              }
            });
            const result = await this.fetchSubjectScopeCheck(departments, 'depart');
            if (result && result.length) {
              const hasSelectedDepartments = [...this.hasSelectedDepartments, ...this.hasSelectedManualDepartments];
              const departTemp = result.filter((item) => {
                return !hasSelectedDepartments.map((subItem) =>
                  subItem.id.toString()).includes(item.id.toString());
              });
              this.hasSelectedManualDepartments.push(...departTemp);
              this.hasSelectedDepartments.push(...departTemp);
              // 备份一份粘贴板里的内容，清除组织的数据，在过滤掉组织的数据
              let clipboardValue = _.cloneDeep(this.manualValue);
              // 处理不相连的数据之间存在特殊符号的情况
              clipboardValue = clipboardValue
                .split(this.regValue)
                .filter((item) => item !== '' && item !== curData)
                .join('\n');
              this.manualValue = _.cloneDeep(clipboardValue);
            }
          }
        }
      },

      async handleSearchOrgAndUser () {
        let manualInputValue = _.cloneDeep(this.manualValue.split(this.regValue));
        manualInputValue = manualInputValue.filter((item) => item !== '' && getUsername(item) !== '');
        for (let i = 0; i < manualInputValue.length; i++) {
          const keyword = getUsername(manualInputValue[i]);
          const params = {
            keyword,
            is_exact: false
          };
          try {
            if (manualInputValue.length < 10) {
              const { data } = await this.$store.dispatch('organization/getSearchOrganizations', params);
              await this.formatSearchData(data, manualInputValue[i]);
            } else {
              this.$store.dispatch('organization/getSearchOrganizations', params).then(async ({ data }) => {
                this.formatSearchData(data, manualInputValue[i]);
              });
            }
          } catch (e) {
            console.error(e);
            this.messageAdvancedError(e);
          }
        }
        this.manualInputError = !!this.manualValue.length;
      },

      async handleAddManualUser () {
        this.fetchRegOrgData();
        this.manualAddLoading = true;
        try {
          const url = this.isRatingManager ? 'role/queryRolesUsers' : 'organization/verifyManualUser';
          const res = await this.$store.dispatch(url, {
            usernames: this.filterUserList.map((item) => {
              return getUsername(item);
            })
          });
          const temps = res.data.filter((item) => {
            this.$set(item, 'type', 'user');
            this.$set(item, 'full_name', item.departments && item.departments.length ? item.departments.join(';') : '');
            return !this.hasSelectedUsers.map((subItem) => subItem.username).includes(item.username);
          });
          this.hasSelectedUsers.push(...temps);
          this.hasSelectedManualUsers.push(...temps);
          if (res.data.length) {
            this.usernameList = res.data.map((item) => item.username);
            // 保存原有格式
            let formatStr = _.cloneDeep(getUsername(this.manualValue));
            this.usernameList.forEach((item) => {
              // 去掉之前有查全局的写法， 如果username有多个重复的item, 比如shengjieliu03@shengjietest.com、shengjieliu05的时候/g就会有问题
              // formatStr = formatStr.replace(this.evil('/' + item + '(;\\n|\\s\\n|)/g'), '');

              // 处理既有部门又有用户且不连续相同类型的展示数据 .split(/，|,|；|;|、|\n|\s/)
              formatStr = formatStr
                .replace(this.evil('/' + item + '(，|,|；|;|、|\\||\\n|\\s\\n|)/'), '')
                // .replace('\n\n', '\n')
                // .replace('\s\s', '\s')
                .replace(/(\s*\r?\n\s*)+/g, '\n')
                .replace(';;', '');
              // 处理复制全部用户不相连的两个不在授权范围内的用户存在空字符
              formatStr = formatStr
                .split(this.regValue)
                .filter((item) => item !== '')
                .join('\n');
            });
            // 处理只选择全部符合条件的用户，还存在特殊符号的情况
            if (formatStr === '\n' || formatStr === '\s' || formatStr === ';') {
              formatStr = '';
            }
            this.manualValue = _.cloneDeep(formatStr);
            if (this.isStaff) {
              // 兼容staff角色不处理部门类的数据
              this.manualInputError = !!this.manualValue;
              this.getDiffSystemOrgData();
              this.fetchManualTableData();
              return;
            }
            this.formatOrgAndUser();
          } else {
            if (this.isStaff) {
              this.manualInputError = !!this.manualValue;
              this.getDiffSystemOrgData();
              return;
            }
            this.formatOrgAndUser();
          }
        } catch (e) {
          console.error(e);
          this.messageAdvancedError(e);
        } finally {
          this.manualAddLoading = false;
        }
      },

      // 处理只复制部门或者部门和用户一起复制情况
      async formatOrgAndUser () {
        if (this.manualValue && !this.isStaff) {
          // 校验查验失败的数据是不是属于部门
          const departData = _.cloneDeep(this.manualValue.split(this.regValue));
          const departGroups = this.filterDepartList.filter((item) => departData.includes(item));
          if (departGroups.length) {
            if (this.getGroupAttributes && this.getGroupAttributes().source_from_role) {
              this.messageWarn(this.$t(`m.common['管理员组不能添加部门']`), 3000);
              this.getDiffSystemOrgData();
              this.fetchManualTableData();
              this.manualInputError = true;
              return;
            }
            // 重新组装粘贴的部门数据
            const list = this.manualOrgList.map((item) => {
              return {
                id: Number(item.slice(item.indexOf('{') + 1, item.indexOf('}'))),
                name: item.slice(item.indexOf('}') + 1, item.indexOf('&') > -1 ? item.indexOf('&') : item.length),
                count: item.slice(item.indexOf('&count=') + 7, item.indexOf('&type=')),
                full_name: item.slice(item.indexOf('&full_name=') + 11, item.indexOf('&count=')),
                type: 'depart',
                showCount: true
              };
            });
            const result = await this.fetchSubjectScopeCheck(list);
            if (result && result.length) {
              const hasSelectedDepartments = [...this.hasSelectedDepartments, ...this.hasSelectedManualDepartments];
              const departTemp = result.filter((item) => {
                return !hasSelectedDepartments.map((subItem) =>
                  subItem.id.toString()).includes(item.id.toString());
              });
              this.hasSelectedManualDepartments.push(...departTemp);
              this.hasSelectedDepartments.push(...departTemp);
              // 备份一份粘贴板里的内容，清除组织的数据，在过滤掉组织的数据
              let clipboardValue = _.cloneDeep(this.manualValue);
              this.manualOrgList.forEach((item) => {
                const displayValue = item.slice(
                  item.indexOf('{'),
                  item.indexOf('&') > -1 ? item.indexOf('&') : item.length
                );
                const isScopeOrg = result
                  .map((depart) => String(depart.id))
                  .includes(item.slice(item.indexOf('{') + 1, item.indexOf('}')));
                if (clipboardValue.split(this.regValue).includes(displayValue) && isScopeOrg) {
                  clipboardValue = clipboardValue.replace(displayValue, '');
                }
              });
              // 处理不相连的数据之间存在特殊符号的情况
              clipboardValue = clipboardValue
                .split(this.regValue)
                .filter((item) => item !== '')
                .join('\n');
              this.manualValue = _.cloneDeep(clipboardValue);
              // this.manualInputError = !!this.manualValue.length;
            } else {
              if (this.isStaff) {
                this.manualInputError = !!this.manualValue;
                return;
              }
              // this.manualInputError = true;
            }
          } else {
            if (this.isStaff) {
              this.manualInputError = !!this.manualValue;
              return;
            }
          }
        }
        if (this.manualValue && !this.isStaff) {
          await this.handleSearchOrgAndUser();
        }
        this.getDiffSystemOrgData();
        this.fetchManualTableData();
      },

      // 校验部门/用户范围是否满足条件
      async fetchSubjectScopeCheck (payload, mode) {
        // 如果业务场景是扩大授权人员边界范围则不需要调用接口校验授权范围
        if (this.isUnLimitedScope) {
          return payload;
        }
        const subjects = payload.map((item) => {
          const { id, type, username } = item;
          const typeMap = {
            depart: () => {
              return {
                type: 'department',
                id
              };
            },
            user: () => {
              return {
                type: 'user',
                id: username
              };
            }
          };
          return typeMap[type || mode]();
        });
        try {
          const { code, data } = await this.$store.dispatch('organization/getSubjectScopeCheck', { subjects });
          if (code === 0 && data) {
            const idList = data.map((v) => v.id);
            const result = payload.filter((item) => {
              if (item.type === 'depart') {
                item.type = 'department';
              }
              return data.map((v) => v.type).includes(item.type)
                && (idList.includes(String(item.id)) || idList.includes(item.username));
            });
            return result;
          }
        } catch (e) {
          this.messageAdvancedError(e);
        }
      },

      // 蓝盾侧限制手动输入添加限制的部门
      getDiffSystemOrgData () {
        if (this.isDisabledOrgPage) {
          // 获取蓝盾侧限制选中的组织架构
          const disabledDeparts = this.hasSelectedManualDepartments.filter((v) => this.isLimitSelectNode(v));
          const disabledUsers = this.hasSelectedManualUsers.filter((v) => this.isLimitSelectNode(v));
          const disabledList = [...disabledDeparts, ...disabledUsers];
          if (disabledList.length) {
            const names = disabledList.map(v => v.name).join();
            this.isShowLimitDialog = true;
            this.limitOrgNodeTip = this.$t(`m.info['手动输入蓝盾侧限制勾选组织架构提示']`, { value: names });
          }
          this.hasSelectedManualDepartments = this.hasSelectedManualDepartments.filter((v) =>
            !this.isLimitSelectNode(v)
          );
          this.hasSelectedDepartments = this.hasSelectedDepartments.filter((v) =>
            !this.isLimitSelectNode(v)
          );
          this.hasSelectedManualUsers = this.hasSelectedManualUsers.filter((v) => !this.isLimitSelectNode(v));
          this.hasSelectedUsers = this.hasSelectedUsers.filter((v) => !this.isLimitSelectNode(v));
        }
        this.manualTableListStorage = [...this.hasSelectedManualDepartments, ...this.hasSelectedManualUsers];
        this.manualTableList = _.cloneDeep(this.manualTableListStorage);
      },

      handleKeyup () {
        // 当搜索的结果数据小于10条时才支持键盘上下键选中
        if (!this.isBeingSearch || this.searchedResult.length > 10) {
          return;
        }
        const len = this.$refs.searchedResultsRef.renderData.length;
        this.focusItemIndex--;
        this.focusItemIndex = this.focusItemIndex < 0 ? -1 : this.focusItemIndex;
        if (this.focusItemIndex === -1) {
          this.focusItemIndex = len - 1;
        }
      },

      handleKeydown () {
        // 当搜索的结果数据小于10条时才支持键盘上下键选中
        if (!this.isBeingSearch || this.searchedResult.length > 10) {
          return;
        }
        const len = this.$refs.searchedResultsRef.renderData.length;
        this.focusItemIndex++;
        this.focusItemIndex = this.focusItemIndex > len - 1 ? len : this.focusItemIndex;
        if (this.focusItemIndex === len) {
          this.focusItemIndex = 0;
        }
      },

      handleShowLimitDialog ({ title }) {
        this.limitOrgNodeTip = title;
        this.isShowLimitDialog = true;
      },

      handleDeadlineChange (payload) {
        this.expiredAt = payload;
      },

      async fetchManagerOrg (treeLoading = false, dialogLoading = true) {
        await this.isRatingManager
          ? this.fetchRoleSubjectScope(treeLoading, dialogLoading)
          : this.fetchCategories(treeLoading, dialogLoading);
      },

      async fetchMemberList () {
        if (!this.curId) {
          await this.fetchManagerOrg();
          return;
        }
        try {
          const params = {
            id: this.curId,
            limit: 1000,
            offset: 0
          };
          let url = 'userGroup/getUserGroupMemberList';
          if (['memberTemplate'].includes(this.routeMode)) {
            url = 'memberTemplate/getSubjectTemplateMembers';
          }
          const { data } = await this.$store.dispatch(url, params);
          const results = data.results || [];
          this.defaultDepartments = results.filter((item) => item.type === 'department');
          this.defaultUsers = results.filter((item) => item.type === 'user');
          await this.fetchManagerOrg();
        } catch (e) {
          this.messageAdvancedError(e);
        } finally {
          this.requestQueue.shift();
        }
      },

      async fetchCategoriesList () {
        try {
          await this.fetchManagerOrg();
        } catch (e) {
          this.messageAdvancedError(e);
        } finally {
          this.requestQueue.shift();
        }
      },

      async fetchRoleSubjectScope (isTreeLoading = false, isDialogLoading = false) {
        this.treeLoading = isTreeLoading;
        try {
          const { code, data } = await this.$store.dispatch('role/getRoleSubjectScope');
          const departments = [...data];
          this.isAllFlag = departments.some((item) => item.type === '*' && item.id === '*');
          if (this.isAllFlag) {
            this.fetchCategories(false, true);
            return;
          }
          this.emptyData = formatCodeData(code, this.emptyData, departments.length === 0);
          departments.forEach((child) => {
            child.visiable = true;
            child.level = 0;
            child.loading = false;
            child.showRadio = true;
            child.isSelected = false;
            child.expanded = false;
            child.disabled = false;
            child.type = child.type === 'user' ? 'user' : 'depart';
            child.count = child.recursive_member_count;
            child.showCount = child.type !== 'user';
            child.async = child.child_count > 0 || child.member_count > 0;
            child.isNewMember = false;
            child.parentNodeId = '';
            if (this.isLimitSelectNode(child)) {
              child.limitOrgNodeTip = this.$t(`m.dialog['用户范围过大，请重新选择']`);
            }
            if (child.async && !child.count) {
              child.count = (child.child_count || 0) + (child.member_count || 0);
            }
            if (child.type === 'user') {
              child.username = child.id;
              if (this.hasSelectedUsers.length > 0) {
                child.isSelected = this.hasSelectedUsers.map((item) => item.id).includes(child.id);
              }
              if (this.defaultUsers.length && this.defaultUsers.map((item) => item.id).includes(child.id)) {
                child.isSelected = true;
                child.disabled = true;
              }
            }
            if (child.type === 'depart') {
              if (this.hasSelectedDepartments.length > 0) {
                child.isSelected = this.hasSelectedDepartments.map((item) => item.id).includes(child.id);
              }
              if (
                this.defaultDepartments.length > 0
                && this.defaultDepartments.map((item) => item.id).includes(child.id.toString())
              ) {
                child.isSelected = true;
                child.disabled = true;
              }
            }
          });
          this.treeList = _.cloneDeep(departments);
        } catch (e) {
          console.error(e);
          const { code } = e;
          this.emptyData = formatCodeData(code, this.emptyData);
          this.messageAdvancedError(e);
        } finally {
          this.treeLoading = false;
          if (isDialogLoading) {
            this.requestQueue.shift();
          }
        }
      },

      async fetchCategories (isTreeLoading = false, isDialogLoading = false) {
        this.treeLoading = isTreeLoading;
        try {
          const { code, data } = await this.$store.dispatch('organization/getCategories');
          this.emptyData = formatCodeData(code, this.emptyData, data.length === 0);
          const categories = [...data];
          categories.forEach((item, index) => {
            item.visiable = true;
            item.level = 0;
            item.showRadio = false;
            item.isSelected = false;
            item.expanded = false;
            item.count = 0;
            item.disabled = !item.departments || item.departments.length < 1;
            item.type = 'depart';
            item.showCount = false;
            item.async = item.departments && item.departments.length > 0;
            item.isNewMember = false;
            item.loading = false;
            item.isSelected = false;
            item.parentNodeId = '';
            item.id = `${item.id}&${item.level}`;
            if (item.departments && item.departments.length > 0) {
              item.departments.forEach((child, childIndex) => {
                child.visiable = false;
                child.level = 1;
                child.loading = false;
                child.showRadio = true;
                child.isSelected = false;
                child.expanded = false;
                child.disabled = false;
                child.showCount = true;
                child.type = 'depart';
                child.count = child.recursive_member_count;
                child.async = child.child_count > 0 || child.member_count > 0;
                child.isNewMember = false;
                child.parentNodeId = item.id;
                child.full_name = `${item.name}${this.$t(`m.common['：']`)}${child.name}`;
                if (this.isLimitSelectNode(child)) {
                  child.limitOrgNodeTip = this.$t(`m.dialog['用户范围过大，请重新选择']`);
                }
                if (child.async && !child.count) {
                  child.count = (child.child_count || 0) + (child.member_count || 0);
                }
                if (this.hasSelectedDepartments.length) {
                  child.isSelected = this.hasSelectedDepartments.map((item) => item.id).includes(child.id);
                } else {
                  child.isSelected = false;
                }

                if (
                  this.defaultDepartments.length > 0
                  && this.defaultDepartments.map((item) => item.id).includes(child.id.toString())
                ) {
                  child.isSelected = true;
                  child.disabled = true;
                }
              });
              item.children = _.cloneDeep(item.departments);
            }
          });
          this.treeList = _.cloneDeep(categories);
        } catch (e) {
          console.error(e);
          const { code } = e;
          this.emptyData = formatCodeData(code, this.emptyData);
          this.messageAdvancedError(e);
        } finally {
          this.treeLoading = false;
          if (isDialogLoading) {
            this.requestQueue.shift();
          }
        }
      },

      async handleOnSelected (newVal, node) {
        if (newVal) {
          if (node.type === 'user') {
            this.hasSelectedUsers.push(node);
          } else {
            this.hasSelectedDepartments.push(node);
          }
        } else {
          if (node.type === 'user') {
            this.hasSelectedUsers = [...this.hasSelectedUsers.filter((item) => item.username !== node.username)];
            this.hasSelectedManualUsers = [...this.hasSelectedManualUsers
              .filter((item) => item.username !== node.username)];
          } else {
            this.hasSelectedDepartments = [...this.hasSelectedDepartments.filter((item) => item.id !== node.id)];
            this.hasSelectedManualDepartments = [...this.hasSelectedManualDepartments
              .filter((item) => item.id !== node.id)];
          }
        }
      },

      async handleSelectedTemplates (payload) {
        this.hasSelectedTemplates = [...payload];
      },

      handleDeleteAll () {
        if (this.searchedUsers.length) {
          this.searchedUsers.forEach((search) => {
            search.isSelected = false;
          });
        }
        if (this.searchedDepartment.length) {
          this.searchedDepartment.forEach((organ) => {
            organ.isSelected = false;
          });
        }
        this.hasSelectedUsers.splice(0, this.hasSelectedUsers.length, ...[]);
        this.hasSelectedDepartments.splice(0, this.hasSelectedDepartments.length, ...[]);
        this.hasSelectedManualUsers.splice(0, this.hasSelectedManualUsers.length, ...[]);
        this.hasSelectedManualDepartments.splice(0, this.hasSelectedManualDepartments.length, ...[]);
        this.hasSelectedTemplates.splice(0, this.hasSelectedTemplates.length, ...[]);
        this.$refs.memberTreeRef && this.$refs.memberTreeRef.clearAllIsSelectedStatus();
        this.$refs.memberTableRef
          && this.$refs.memberTableRef.$refs
          && this.$refs.memberTableRef.$refs.templateTableRef.clearSelection();
        this.fetchManualTableData();
      },

      handleConditionSelcted (payload) {
        this.$refs.dropdown.hide();
        this.searchConditionValue = payload.id;
        this.handleSearch();
      },

      async handleSearch () {
        if (this.keyword === '') {
          return;
        }
        if (this.focusItemIndex !== -1) {
          this.$refs.searchedResultsRef.setCheckStatusByIndex();
          return;
        }
        this.treeList.splice(0, this.treeList.length, ...[]);
        this.isBeingSearch = true;
        this.treeLoading = true;
        this.searchedResult.splice(0, this.searchedResult.length, ...[]);
        this.searchedDepartment.splice(0, this.searchedDepartment.length, ...[]);
        this.searchedUsers.splice(0, this.searchedUsers.length, ...[]);
        const defaultDepartIds = [...this.defaultDepartments.map((item) => item.id)];
        const defaultUserIds = [...this.defaultUsers.map((item) => item.id)];
        const departIds = [...this.hasSelectedDepartments.map((item) => item.id)];
        const userIds = [...this.hasSelectedUsers.map((item) => item.username)];
        const params = {
          keyword: this.keyword,
          is_exact: this.searchConditionValue === 'exact'
        };
        try {
          const { code, data } = await this.$store.dispatch('organization/getSearchOrganizations', params);
          const { users, departments } = data;
          if (data.is_too_much) {
            this.isShowTooMuch = true;
            return;
          }
          this.isShowTooMuch = false;
          if (departments.length > 0) {
            data.departments.forEach((depart) => {
              depart.type = 'depart';
              depart.showRadio = true;
              depart.showCount = true;
              depart.disabled = false;
              depart.isSelected = false;
              depart.count = depart.recursive_member_count;
              if (this.isLimitSelectNode(depart)) {
                depart.limitOrgNodeTip = this.$t(`m.dialog['用户范围过大，请重新选择']`);
              }
              if (departIds.length && departIds.includes(depart.id)) {
                depart.isSelected = true;
              }
              if (defaultDepartIds.length && defaultDepartIds.includes(depart.id.toString())) {
                depart.isSelected = true;
                depart.disabled = true;
              }
            });
            this.searchedDepartment.splice(0, this.searchedDepartment.length, ...data.departments);
          }
          if (users.length > 0) {
            data.users.forEach((user) => {
              user.id = guid();
              user.showRadio = true;
              user.disabled = false;
              user.isSelected = false;
              user.type = 'user';
              user.full_name = '';
              if (this.isLimitSelectNode(user)) {
                user.limitOrgNodeTip = this.$t(`m.dialog['用户范围过大，请重新选择']`);
              }
              if (user.departments && user.departments.length > 0) {
                user.full_name = user.departments.join(';');
              }
              if (userIds.length && userIds.includes(user.username)) {
                user.isSelected = true;
              }
              if (defaultUserIds.length && defaultUserIds.includes(user.username)) {
                user.disabled = true;
                user.isSelected = true;
              }
            });
            this.searchedUsers.splice(0, this.searchedUsers.length, ...data.users);
          }
          this.searchedResult.splice(
            0,
            this.searchedResult.length,
            ...this.searchedDepartment.concat(this.searchedUsers)
          );
          const isEmpty = users.length === 0 && departments.length === 0;
          this.emptyData.tipType = 'search';
          this.emptyData = formatCodeData(code, this.emptyData, isEmpty);
        } catch (e) {
          console.error(e);
          const { code } = e;
          this.emptyData = formatCodeData(code, this.emptyData);
          this.messageAdvancedError(e);
        } finally {
          this.treeLoading = false;
        }
      },

      handleExpanded (payload) {
        if (this.isRatingManager && !this.isAllFlag) {
          return;
        }
        const flag = this.treeList.some((item) => item.parentNodeId === payload.id);
        if (payload.level === 0 && !flag) {
          const curIndex = this.treeList.findIndex((item) => item.id === payload.id);
          if (curIndex !== -1) {
            const children = _.cloneDeep(this.treeList[curIndex].children);
            if (children && children.length > 0) {
              children.forEach((item) => {
                item.visiable = true;
              });
              this.treeList.splice(curIndex + 1, 0, ...children);
            }
          }
        }
      },

      async handleRemoteLoadNode (payload) {
        if (payload.level === 0 && !this.isRatingManager) {
          return;
        }
        payload.loading = true;
        try {
          const res = await this.$store.dispatch('organization/getOrganizations', { departmentId: payload.id });
          // const { child_count, children, id, member_count, members, name, recursive_member_count } = res.data
          const { children, members } = res.data;
          if (children.length < 1 && members.length < 1) {
            payload.expanded = false;
            return;
          }
          const curIndex = this.treeList.findIndex((item) => item.id === payload.id);
          if (curIndex === -1) {
            return;
          }
          const treeList = [];
          treeList.splice(0, 0, ...this.treeList);
          if (children.length > 0) {
            children.forEach((child, childIndex) => {
              child.visiable = payload.expanded;
              child.level = payload.level + 1;
              child.loading = false;
              child.showRadio = true;
              child.isSelected = false;
              child.expanded = false;
              child.showCount = true;
              child.type = 'depart';
              child.disabled = this.disabled;
              child.count = child.recursive_member_count;
              child.async = child.child_count > 0 || child.member_count > 0;
              child.isNewMember = false;
              child.parentNodeId = payload.id;
              child.full_name = `${payload.full_name}/${child.name}`;
              if (this.isLimitSelectNode(child)) {
                child.limitOrgNodeTip = this.$t(`m.dialog['用户范围过大，请重新选择']`);
              }
              if (child.async && !child.count) {
                child.count = (child.child_count || 0) + (child.member_count || 0);
              }
              if (this.hasSelectedDepartments.length > 0) {
                child.isSelected = this.hasSelectedDepartments.map((item) => item.id).includes(child.id);
              }
              if (
                this.defaultDepartments.length > 0
                && this.defaultDepartments.map((item) => item.id).includes(child.id.toString())
              ) {
                child.isSelected = true;
                child.disabled = true;
              }
            });
          }
          if (members.length > 0) {
            members.forEach((child, childIndex) => {
              child.visiable = payload.expanded;
              child.level = payload.level + 1;
              child.loading = false;
              child.showRadio = true;
              child.isSelected = false;
              child.expanded = false;
              child.disabled = this.disabled;
              child.type = 'user';
              child.count = 0;
              child.showCount = false;
              child.async = false;
              child.isNewMember = false;
              child.parentNodeId = payload.id;
              // child.full_name = `${payload.full_name}/${child.name}`;
              child.full_name = payload.full_name;
              // parentNodeId + username 组合成id
              child.id = `${child.parentNodeId}${child.username}`;
              if (this.isLimitSelectNode(child)) {
                child.limitOrgNodeTip = this.$t(`m.dialog['用户范围过大，请重新选择']`);
              }
              if (this.hasSelectedUsers.length > 0) {
                child.isSelected
                  = this.hasSelectedUsers.map((item) => item.id).includes(child.id)
                    || this.hasSelectedUsers.map((item) => `${child.parentNodeId}${item.username}`).includes(child.id);
              }
              const existSelectedNode = this.treeList.find((item) =>
                item.isSelected && item.username === child.username
              );
              const defaultSelectedUser = this.defaultUsers.map((item) => item.id).includes(child.username);
              const isExistSelectedUser = existSelectedNode || defaultSelectedUser;
              if (isExistSelectedUser) {
                child.isSelected = true;
                child.disabled = true;
              }
            });
          }
          const loadChildren = children.concat([...members]);
          treeList.splice(curIndex + 1, 0, ...loadChildren);
          this.treeList.splice(0, this.treeList.length, ...treeList);
          if (!payload.children) {
            payload.children = [];
          }
          payload.children.splice(0, payload.children.length, ...loadChildren);
        } catch (e) {
          console.error(e);
          this.messageAdvancedError(e);
        } finally {
          setTimeout(() => {
            payload.loading = false;
          }, 300);
        }
      },

      handleDelete (item, type) {
        if (this.isAll) {
          return;
        }
        if (this.isBeingSearch) {
          if (this.searchedUsers.length) {
            this.searchedUsers.forEach((search) => {
              if (search.username === item.username) {
                search.isSelected = false;
              }
            });
          }
          if (this.searchedDepartment.length) {
            this.searchedDepartment.forEach((organ) => {
              if (organ.id === item.id) {
                organ.isSelected = false;
              }
            });
          }
        } else {
          this.tabActive === 'organization' && this.$refs.memberTreeRef.setSingleSelectedStatus(item.id, false);
        }
        if (type === 'user') {
          this.hasSelectedUsers = [...this.hasSelectedUsers.filter((user) => user.username !== item.username)];
          this.hasSelectedManualUsers
            = [...this.hasSelectedManualUsers.filter((user) => user.username !== item.username)];
        } else {
          // eslint-disable-next-line max-len
          this.hasSelectedDepartments = [...this.hasSelectedDepartments.filter((organ) => organ.id !== item.id)];
          this.hasSelectedManualDepartments
            = [...this.hasSelectedManualDepartments.filter((organ) => organ.id !== item.id)];
        }
        if (type === 'template') {
          this.hasSelectedTemplates = [...this.hasSelectedTemplates.filter((v) => String(item.id) !== String(v.id))];
        }
        this.fetchManualTableData();
      },

      async handleSearchResultSelected (newVal, oldVal, localVal, item) {
        if (item.type === 'user') {
          this.handleSearchUserSelected(newVal, item);
        } else {
          if (newVal) {
            this.hasSelectedDepartments.push(item);
          } else {
            this.hasSelectedDepartments = this.hasSelectedDepartments.filter((organ) => organ.id !== item.id);
            this.hasSelectedManualDepartments
              = this.hasSelectedManualDepartments.filter((organ) => organ.id !== item.id);
          }
        }
      },

      handleSearchUserSelected (newVal, item) {
        if (newVal) {
          this.hasSelectedUsers.push(item);
        } else {
          this.hasSelectedUsers = this.hasSelectedUsers.filter((user) => user.username !== item.username);
          this.hasSelectedManualUsers = this.hasSelectedManualUsers.filter((user) => user.username !== item.username);
        }
      },

      handleTableSearch () {
        this.emptyTableData.tipType = 'search';
        this.manualTableList = this.manualTableListStorage.filter((item) => {
          return (
            item.name.indexOf(this.tableKeyWord) > -1
            || (item.username && item.username.indexOf(this.tableKeyWord) > -1));
        });
        if (!this.manualTableList.length) {
          this.emptyTableData = formatCodeData(0, this.emptyTableData, true);
        }
        this.fetchManualTableData();
      },

      handleClearSearch () {
        this.tableKeyWord = '';
        this.manualTableList = _.cloneDeep(this.manualTableListStorage);
        if (!this.manualTableList.length) {
          this.emptyTableData = Object.assign({}, {
            type: 'empty',
            text: '请先从左侧输入并解析',
            tip: '',
            tipType: ''
          });
          return;
        }
        this.fetchManualTableData();
      },
      
      handleAfterLeave () {
        this.isPrev = true;
        this.expiredAt = 15552000;
        this.keyword = '';
        this.treeLoading = false;
        this.isBeingSearch = false;
        this.hasSelectedUsers.splice(0, this.hasSelectedUsers.length, ...[]);
        this.hasSelectedDepartments.splice(0, this.hasSelectedDepartments.length, ...[]);
        this.searchedDepartment.splice(0, this.searchedDepartment.length, ...[]);
        this.searchedUsers.splice(0, this.searchedUsers.length, ...[]);
        this.searchedResult.splice(0, this.searchedResult.length, ...[]);
        this.treeList.splice(0, this.treeList.length, ...[]);
        this.requestQueue = ['categories', 'memberList'];
        this.focusItemIndex = -1;
        this.$refs.memberTreeRef && this.$refs.memberTreeRef.clearAllIsSelectedStatus();
        this.searchConditionValue = 'fuzzy';
        this.tabActive = 'organization';
        this.manualValue = '';
        this.manualAddLoading = false;
        this.manualInputError = false;
        this.manualValueBackup = [];
        this.manualTableList = [];
        this.manualTableListStorage = [];
        this.hasSelectedManualDepartments = [];
        this.hasSelectedManualUsers = [];
        this.hasSelectedTemplates = [];
        this.defaultDepartments = [];
        this.defaultUsers = [];
        this.$refs.memberTableRef
          && this.$refs.memberTableRef.$refs
          && this.$refs.memberTableRef.$refs.templateTableRef.clearSelection();
        this.tableKeyWord = '';
        this.$emit('update:show', false);
        this.$emit('on-after-leave');
      },

      handleCancel () {
        this.$emit('on-cancel');
      },

      handleNextStep () {
        if (this.getGroupAttributes
          && this.getGroupAttributes().source_from_role
          && this.hasSelectedTemplates.length > 0) {
          this.messageWarn(this.$t(`m.common['管理员组不能添加人员模板']`), 3000);
          return;
        }
        this.isPrev = false;
      },

      handlePrevStep () {
        this.expiredAt = 15552000;
        this.isPrev = true;
      },

      handleSave () {
        if (this.getGroupAttributes
          && this.getGroupAttributes().source_from_role
          && this.hasSelectedTemplates.length > 0) {
          this.messageWarn(this.$t(`m.common['管理员组不能添加人员模板']`), 3000);
          return;
        }
        const params = {
          users: this.hasSelectedUsers,
          departments: this.hasSelectedDepartments,
          templates: this.hasSelectedTemplates,
          isAll: this.isAll
        };
        if (this.showExpiredAt) {
          params.expiredAt = this.expiredAt;
          if (this.expiredAt !== 4102444800) {
            params.policy_expired_at = this.expiredAt;
          } else {
            params.policy_expired_at = this.expiredAt;
          }
        }
        this.$emit('on-sumbit', params);
      },

      evil (fn) {
        const Fn = Function;
        return new Fn('return ' + fn)();
      },

      async handleSkip () {
        const routeData = this.$router.resolve({
          name: 'authorBoundaryEditFirstLevel',
          params: { id: this.$store.getters.curRoleId }
        });
        window.open(routeData.href, '_blank');
      },

      fetchSelectedGroups (type, payload, row) {
        const typeMap = {
          multiple: async () => {
            const isChecked = payload.length && payload.indexOf(row) !== -1;
            if (['depart', 'department'].includes(row.type)) {
              if (isChecked) {
                const hasSelectedDepart = [...this.hasSelectedDepartments, ...this.hasSelectedManualDepartments];
                let hasSelectedDepartIds = [];
                if (hasSelectedDepart.length) {
                  hasSelectedDepartIds = hasSelectedDepart.map((v) => String(v.id));
                }
                if (!hasSelectedDepartIds.includes(String(row.id))) {
                  this.hasSelectedDepartments.push(row);
                  this.hasSelectedManualDepartments.push(row);
                }
              } else {
                this.hasSelectedDepartments = this.hasSelectedDepartments.filter(
                  (item) => item.id.toString() !== row.id.toString()
                );
                this.hasSelectedManualDepartments = this.hasSelectedManualDepartments.filter(
                  (item) => item.id.toString() !== row.id.toString()
                );
              }
            }
            if (['user'].includes(row.type)) {
              if (isChecked) {
                const hasSelectedUsers = [...this.hasSelectedUsers, ...this.hasSelectedManualUsers];
                let hasSelectedUsersIds = [];
                if (hasSelectedUsers.length) {
                  hasSelectedUsersIds = hasSelectedUsers.map((v) => `${v.username}${v.name}`);
                }
                if (!hasSelectedUsersIds.includes(`${row.username}${row.name}`)) {
                  this.hasSelectedUsers.push(row);
                  this.hasSelectedManualUsers.push(row);
                }
              } else {
                this.hasSelectedUsers = this.hasSelectedUsers.filter(
                  (item) => `${item.username}${item.name}` !== `${row.username}${row.name}`
                );
                this.hasSelectedManualUsers = this.hasSelectedManualUsers.filter(
                  (item) => `${item.username}${item.name}` !== `${row.username}${row.name}`
                );
              }
            }
          },
          all: async () => {
            const isAllCheck = payload.length > 0;
            this.manualTableList.forEach((item) => {
              if (['depart', 'department'].includes(item.type)) {
                if (isAllCheck) {
                  const hasSelectedDepart = [...this.hasSelectedDepartments, ...this.hasSelectedManualDepartments];
                  let hasSelectedDepartIds = [];
                  if (hasSelectedDepart.length) {
                    hasSelectedDepartIds = hasSelectedDepart.map((v) => String(v.id));
                  }
                  if (!hasSelectedDepartIds.includes(String(item.id))) {
                    this.hasSelectedDepartments.push(item);
                    this.hasSelectedManualDepartments.push(item);
                  }
                } else {
                  this.hasSelectedDepartments = this.hasSelectedDepartments.filter(
                    (v) => item.id.toString() !== v.id.toString()
                  );
                  this.hasSelectedManualDepartments = this.hasSelectedManualDepartments.filter(
                    (v) => item.id.toString() !== v.id.toString()
                  );
                }
              }
              if (['user'].includes(item.type)) {
                if (isAllCheck) {
                  const hasSelectedUsers = [...this.hasSelectedUsers, ...this.hasSelectedManualUsers];
                  let hasSelectedUsersIds = [];
                  if (hasSelectedUsers.length) {
                    hasSelectedUsersIds = hasSelectedUsers.map((v) => `${v.username}${v.name}`);
                  }
                  if (!hasSelectedUsersIds.includes(`${item.username}${item.name}`)) {
                    this.hasSelectedUsers.push(item);
                    this.hasSelectedManualUsers.push(item);
                  }
                } else {
                  this.hasSelectedUsers = this.hasSelectedUsers.filter(
                    (v) => `${item.username}${item.name}` !== `${v.username}${v.name}`
                  );
                  this.hasSelectedManualUsers = this.hasSelectedManualUsers.filter(
                    (v) => `${item.username}${item.name}` !== `${v.username}${v.name}`
                  );
                }
              }
            });
          }
        };
        return typeMap[type]();
      },

      handleSelectChange (selection, row) {
        this.fetchSelectedGroups('multiple', selection, row);
      },

      handleSelectAllChange (selection) {
        this.fetchSelectedGroups('all', selection);
      }
    }
  };
</script>
<style lang="postcss" scoped>
.iam-add-member-dialog {
  .title {
    line-height: 26px;
    color: #313238;
    .member-title {
      display: inline-block;
      max-width: 470px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      vertical-align: top;
    }
    .expired-at-title {
      display: inline-block;
      max-width: 290px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      vertical-align: top;
    }
  }
  .limit-wrapper {
    float: left;
    margin-top: 5px;
  }
  .add-member-content-wrapper {
    /* height: 383px; */
    height: 510px;
    .left {
      /* display: inline-block; */
      /* width: 320px; */
      /* height: 383px; */
      width: 680px;
      height: 510px;
      border-right: 1px solid #dcdee5;
      float: left;
      .tab-wrapper {
        position: relative;
        /* top: -15px; */
        top: 0;
        display: flex;
        justify-content: flex-start;
        height: 42px;
        line-height: 42px;
        /* border-bottom: 1px solid #d8d8d8; */
        background-color: #fafbfd;
        border: 1px solid #dcdee5;
        border-right: 0;
        margin-bottom: 15px;
        .tab-item {
          min-width: 97px;
          padding: 0 5px;
          text-align: center;
          color: #63656e;
          border-right: 1px solid #dcdee5;
          position: relative;
          cursor: pointer;
          &-active {
            background-color: #ffffff;
            margin-bottom: -1px;
          }
          .active-line {
            position: absolute;
            bottom: -1px;
            left: 0;
            width: 100%;
            height: 2px;
            background: #3a84ff;
          }
        }
      }
      .member-tree-wrapper {
        /* min-height: 309px; */
        min-height: 400px;
        margin: 0 24px;
      }
      .tree {
        /* max-height: 309px; */
        max-height: 400px;
        overflow: auto;
        &::-webkit-scrollbar {
          width: 4px;
          background-color: lighten(transparent, 80%);
        }
        &::-webkit-scrollbar-thumb {
          height: 5px;
          border-radius: 2px;
          background-color: #e6e9ea;
        }
      }
      .search-input {
        margin: 0 24px 5px 24px;
        /* margin-bottom: 5px; */
        /* width: 310px; */
        width: 632px;
        height: 32px;
        line-height: normal;
        color: #63656e;
        background-color: #fff;
        border-radius: 2px;
        font-size: 12px;
        border: 1px solid #c4c6cc;
        padding: 0 10px;
        /* text-align: left; */
        vertical-align: middle;
        outline: none;
        resize: none;
        transition: border 0.2s linear;
        &.disabled {
          background-color: #fafbfd;
        }
        &.active {
          border-color: #3a84ff;
        }
        .search-config-icon {
          font-size: 14px;
        }
        .bk-dropdown-menu {
          position: relative;
          /* top: 7px; */
          top: 2px;
          &:hover {
            .search-icon {
              color: #3a84ff;
              cursor: pointer;
            }
          }
          .search-icon {
            font-size: 16px;
          }
        }
        .bk-dropdown-trigger {
          cursor: pointer;
        }
        .bk-dropdown-list {
          li {
            a {
              font-size: 14px;
              &.active {
                background-color: #eaf3ff;
                color: #3a84ff;
              }
            }
          }
        }
      }
      .search-content {
        .too-much-wrapper {
          position: absolute;
          left: 50%;
          top: 50%;
          text-align: center;
          transform: translate(-50%, -50%);
          .much-tips-icon {
            font-size: 21px;
            color: #63656e;
          }
          .text {
            margin-top: 6px;
            font-size: 12px;
            color: #dcdee5;
          }
        }
        .search-empty-wrapper {
          width: 100%;
          position: absolute;
          left: 50%;
          top: 50%;
          text-align: center;
          transform: translate(-50%, -50%);
          img {
            width: 120px;
          }
          .empty-tips {
            position: relative;
            top: -20px;
            font-size: 12px;
            color: #dcdee5;
          }
        }
      }
      .manual-wrapper {
        display: flex;
        &-left {
          padding-left: 24px;
          padding-right: 10px;
          .manual-error-text {
            /* position: absolute; */
            /* width: 320px; */
            width: 248px;
            margin-top: 4px;
            font-size: 12px;
            color: #ff4d4d;
            line-height: 14px;
          }
        }
      }

      .manual-input-alert {
        padding: 0 24px;
        margin-bottom: 10px;
      }
      .template-wrapper {
        padding: 0 24px;
      }
    }
    .right {
      display: inline-block;
      padding-left: 24px;
      width: 280px;
      /* height: 383px; */
      height: 510px;
      background-color: #f5f7fa;
      border-top: 1px solid #dcdee5;
      .result-preview {
        display: flex;
        justify-content: space-between;
        padding: 8px 24px 8px 0px;
        .bk-button-text.is-disabled {
          color: #c4c6cc;
        }
      }
      .header {
        display: flex;
        justify-content: space-between;
        position: relative;
        top: 0;
        /* padding: 8px 24px 8px 14px; */
        padding-right: 24px;
        font-size: 12px;
        word-break: break-all;
        .organization-count,
        .user-count,
        .template-count {
          /* margin-right: 3px; */
          color: #3a84ff;
          font-weight: 700;
        }
      }
      .content {
        position: relative;
        margin: 15px 24px 15px 0;
        /* height: 345px; */
        height: 414px;
        overflow: auto;
        &::-webkit-scrollbar {
          width: 4px;
          background-color: lighten(transparent, 80%);
        }
        &::-webkit-scrollbar-thumb {
          height: 5px;
          border-radius: 2px;
          background-color: #e6e9ea;
        }
        .organization-content {
          background-color: #ffffff;
          .organization-item {
            padding: 5px;
            box-shadow: 0 1px 1px 0 #00000014;
            border-radius: 2px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            &:last-child {
              margin-bottom: 1px;
            }
            &-left {
              width: calc(100% - 30px);
              display: flex;
              align-items: center;
            }
            .organization-name {
              display: inline-block;
              margin-left: 5px;
              /* max-width: 200px; */
              font-size: 12px;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
              vertical-align: top;
              word-break: break-all;
            }
            .delete-depart-icon {
              display: block;
              font-size: 18px;
              margin: 4px 6px 0 0;
              color: #c4c6cc;
              cursor: pointer;
              float: right;
              &:hover {
                color: #3a84ff;
              }
            }
            .user-count {
              color: #c4c6cc;
            }
          }
          .folder-icon {
            font-size: 17px;
            color: #a3c5fd;
          }
        }
        .user-content,
        .template-content {
          background-color: #ffffff;
          .user-item,
          .template-item {
            padding: 5px;
            box-shadow: 0 1px 1px 0 #00000014;
            border-radius: 2px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            .user-item-left,
            .template-item-left {
              display: flex;
              align-items: center;
            }
            .user-name,
            .template-name {
              margin-left: 5px;
              display: inline-block;
              /* max-width: 200px; */
              max-width: 160px;
              font-size: 12px;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
              vertical-align: top;
              word-break: break-all;
            }
            .delete-icon {
              display: block;
              font-size: 18px;
              margin: 4px 6px 0 0;
              color: #c4c6cc;
              cursor: pointer;
              float: right;
              &:hover {
                color: #3a84ff;
              }
            }
          }
          .user-item-bottom {
            margin-bottom: 1px;
          }
          .user-icon {
            font-size: 16px;
            color: #a3c5fd;
          }
        }
        .selected-empty-wrapper {
          position: absolute;
          left: 50%;
          top: 50%;
          transform: translate(-50%, -50%);
          img {
            width: 120px;
          }
        }
      }
    }
  }

  .highlight {
    color: #3a84ff;
    cursor: pointer;
    user-select: none;
  }

  .iam-add-member-search-input-cls {
    position: relative;
    top: 0;
    left: 0;
    /* width: 277px !important; */
    width: 586px !important;
    .bk-form-input {
      height: 29px !important;
      border: none !important;
    }
  }

  .manual-bottom-btn {
    margin-top: 10px;
  }

  .manual-input-wrapper {
    width: 376px;
    margin-bottom: 10px;
  }

  .manual-table-wrapper {
    height: 340px;
    border: none;
  }

  .set-user-deadline {
    padding: 0 24px;
  }
}

/deep/ .bk-dialog-wrapper {
  .bk-dialog {
    top: 100px;
  }
  .bk-dialog-body {
    padding: 0 !important;
  }
}

/deep/ .manual-textarea {
  width: 248px;
  .bk-textarea-wrapper {
    .bk-form-textarea {
      min-height: 300px;
      &::-webkit-scrollbar {
        width: 6px;
        background-color: lighten(transparent, 80%);
      }
      &::-webkit-scrollbar-thumb {
        height: 5px;
        border-radius: 2px;
        background-color: #e6e9ea;
      }
    }
  }
}
</style>
