<template>
  <div class="iam-perm-template-attach-member-wrapper"
    v-bkloading="{ isLoading: tabLoading, opacity: 1 }">
    <bk-table
      v-if="!tabLoading"
      :data="tableList"
      size="small"
      :class="{ 'set-border': tableLoading }"
      ext-cls="perm-template-attach-member-table"
      :max-height="tableHeight"
      :pagination="pagination"
      @page-change="handlePageChange"
      @page-limit-change="handleLimitChange"
      v-bkloading="{ isLoading: tableLoading, opacity: 1 }">
      <!-- <bk-table-column :label="$t(`m.common['ID']`)" width="300">
                <template slot-scope="{ row }">
                    <span :title="`#${row.id}`">{{ '#' + row.id }}</span>
                </template>
            </bk-table-column> -->
      <bk-table-column :label="$t(`m.userGroup['用户组']`)">
        <template slot-scope="{ row }">
          <span class="group-name" :title="row.name" @click.stop="handleView(row)">{{ row.name }}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t(`m.common['操作-table']`)" width="200">
        <template slot-scope="{ row }">
          <bk-button theme="primary" text @click="handleRemove(row)">{{ $t(`m.perm['解除关联']`) }}</bk-button>
        </template>
      </bk-table-column>
      <template slot="empty">
        <ExceptionEmpty
          :type="emptyData.type"
          :empty-text="emptyData.text"
          :tip-text="emptyData.tip"
          :tip-type="emptyData.tipType"
          @on-refresh="handleEmptyRefresh"
        />
      </template>
    </bk-table>

    <delete-dialog
      :show.sync="isShowRemoveDialog"
      :loading="removeLoading"
      :title="$t(`m.dialog['确认移除']`)"
      :sub-title="removeSubTitle"
      @on-after-leave="handleAfterRemoveLeave"
      @on-cancel="hideCancelRemove"
      @on-sumbit="handleSumbitRemove" />

    <perm-sideslider
      :is-show.sync="isShowPermSlider"
      :group-id="curGroupId" />
  </div>
</template>
<script>
  import DeleteDialog from '@/components/iam-confirm-dialog/index.vue';
  import PermSideslider from '../components/render-group-perm-sideslider';
  import { getWindowHeight, formatCodeData } from '@/common/util';

  export default {
    inject: ['showNoticeAlert'],
    components: {
      DeleteDialog,
      PermSideslider
    },
    props: {
      id: {
        type: [String, Number],
        default: ''
      }
    },
    data () {
      return {
        removeLoading: false,
        isShowRemoveDialog: false,
        tableList: [],
        tableLoading: false,
        tabLoading: false,
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        currentBackup: 1,
        removeSubTitle: '',
        currentMember: [],
        isShowPermSlider: false,
        curGroupId: '',
        emptyData: {
          type: '',
          text: '',
          tip: '',
          tipType: ''
        },
        tableHeight: 0
      };
    },
    watch: {
      'pagination.current' (value) {
        this.currentBackup = value;
      }
    },
    created () {
      this.fetchData(true);
    },
    mounted () {
      this.getTableHeight();
      window.addEventListener('resize', this.getTableHeight);
      this.$once('hook:beforeDestroy', () => {
        window.removeEventListener('resize', this.getTableHeight);
      });
    },
    methods: {
      getTableHeight () {
        const defaultHeight = getWindowHeight() - 185;
        this.tableHeight = this.showNoticeAlert && this.showNoticeAlert() ? defaultHeight - 40 : defaultHeight;
      },
      async fetchData (isTabLoading = false, isTableLoading = false) {
        this.tableLoading = isTableLoading;
        this.tabLoading = isTabLoading;
        if (isTabLoading) {
          this.$emit('on-init', true);
        }
        const params = {
          id: this.id,
          types: 'group',
          limit: this.pagination.limit,
          offset: this.pagination.limit * (this.pagination.current - 1)
        };
        try {
          const { code, data } = await this.$store.dispatch('permTemplate/getTemplateMember', params);
          this.pagination.count = data.count;
          this.tableList.splice(0, this.tableList.length, ...(data.results || []));
          this.emptyData = formatCodeData(code, this.emptyData, this.tableList.length === 0);
        } catch (e) {
          console.error(e);
          const { code } = e;
          this.tableList = [];
          this.emptyData = formatCodeData(code, this.emptyData);
          this.messageAdvancedError(e);
        } finally {
          this.tableLoading = false;
          if (isTabLoading) {
            this.tabLoading = false;
            this.$emit('on-init', false);
          }
        }
      },

      handleView ({ id }) {
        this.curGroupId = id;
        this.isShowPermSlider = true;
      },

      handleAfterRemoveLeave () {
        this.currentMember.splice(0, this.currentMember.length, ...[]);
        this.removeSubTitle = '';
      },

      hideCancelRemove () {
        this.isShowRemoveDialog = false;
      },

      async handleSumbitRemove () {
        this.removeLoading = true;
        const params = {
          id: this.id,
          data: {
            members: this.currentMember
          }
        };
        console.warn(params);
        try {
          await this.$store.dispatch('permTemplate/deleteTemplateMember', params);
          this.isShowRemoveDialog = false;
          this.messageSuccess(this.$t(`m.info['移除成功']`), 3000);
          this.fetchData(false, true);
        } catch (e) {
          console.error(e);
          this.messageAdvancedError(e);
        } finally {
          this.removeLoading = false;
        }
      },

      handlePageChange (page) {
        if (this.currentBackup === page) {
          return;
        }
        this.pagination.current = page;
        this.fetchData(false, true);
      },

      handleLimitChange (currentLimit, prevLimit) {
        this.pagination.limit = currentLimit;
        this.pagination.current = 1;
        this.fetchData(false, true);
      },

      handleRemove (payload) {
        this.removeSubTitle = `${this.$t(`m.common['移除']`)}${this.$t(`m.common['【']`)}${payload.name}${this.$t(`m.common['】']`)}${this.$t(`m.common['，']`)}${this.$t(`m.info['该用户组将不再继承对应模板的权限']`)}${this.$t(`m.common['。']`)}`;
        this.currentMember.push({
          type: payload.type,
          id: payload.id
        });
        this.isShowRemoveDialog = true;
      },

      handleEmptyRefresh () {
        this.pagination = Object.assign(this.pagination, {
          current: 1,
          limit: 10
        });
        this.fetchData(false, true);
      }
    }
  };
</script>
<style lang="postcss">
    .iam-perm-template-attach-member-wrapper {
        position: relative;
        height: calc(100vh - 145px);
        .perm-template-attach-member-table {
            border-right: none;
            border-bottom: none;
            &.set-border {
                border-right: 1px solid #dfe0e5;
                border-bottom: 1px solid #dfe0e5;
            }
            tr:hover {
                .user,
                .depart,
                .group {
                    background: #fff;
                }
            }
            .group-name {
                color: #3a84ff;
                cursor: pointer;
                &:hover {
                    color: #699df4;
                }
            }
            .user,
            .group,
            .depart {
                padding: 4px 6px;
                background: #f0f1f5;
                width: max-content;
                border-radius: 2px;
                i {
                    font-size: 14px;
                    color: #c4c6cc;
                }
                .name {
                    display: inline-block;
                    max-width: 350px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    vertical-align: bottom;
                }
            }
        }
    }
</style>
