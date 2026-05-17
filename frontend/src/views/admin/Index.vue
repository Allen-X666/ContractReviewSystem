<template>
  <div class="admin-page">
    <div class="page-header">
      <h1 class="page-title">系统管理</h1>
    </div>

    <div class="admin-content">
      <!-- 左侧菜单 -->
      <div class="admin-sidebar">
        <div
          v-for="item in menuItems"
          :key="item.key"
          :class="['menu-item', { active: activeMenu === item.key }]"
          @click="activeMenu = item.key"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </div>
      </div>

      <!-- 右侧内容 -->
      <div class="admin-main">
        <!-- 法律文档上传 -->
        <div v-if="activeMenu === 'law-upload'" class="admin-section">
          <h3 class="section-title">法律文档上传</h3>
          <div class="upload-area">
            <el-upload
              drag
              action="/api/admin/law/upload"
              :auto-upload="false"
              :on-change="handleLawFileChange"
              :on-remove="handleLawFileRemove"
              :file-list="lawFileList"
              accept=".pdf,.doc,.docx,.md"
              multiple
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 PDF、Word、Markdown 格式文件，单个文件不超过 50MB
                  <el-button type="primary" link size="small" @click="previewExampleFile">
                    <el-icon><View /></el-icon>
                    示例文件
                  </el-button>
                  <div>(请务必按照示例文件格式上传)</div>
                </div>
              </template>
            </el-upload>
          </div>

          <div class="upload-form">
            <el-form :model="lawForm" label-width="100px">
              <el-form-item label="文档类型">
                <el-select v-model="lawForm.type" placeholder="请选择文档类型" style="width: 100%">
                  <el-option label="法律法规" value="law" />
                  <el-option label="司法解释" value="interpretation" />
                  <el-option label="合同范本" value="template" />
                  <el-option label="其他文档" value="other" />
                </el-select>
              </el-form-item>
              <el-form-item label="生效日期">
                <el-date-picker
                  v-model="lawForm.effectiveDate"
                  type="date"
                  placeholder="选择生效日期"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="文档说明">
                <el-input
                  v-model="lawForm.description"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入文档说明"
                />
              </el-form-item>
            </el-form>
          </div>

          <div class="upload-actions">
            <el-button type="primary" :loading="uploading" @click="uploadLawFiles">
              <el-icon><Upload /></el-icon>
              <span>开始上传</span>
            </el-button>
            <el-button @click="clearLawFiles">清空列表</el-button>
          </div>

          <!-- 已上传文档列表 -->
          <div class="uploaded-list">
            <h4>已上传文档</h4>
            <el-table :data="uploadedLaws" style="width: 100%" v-loading="loadingLaws">
              <el-table-column prop="name" label="文档名称" min-width="200" />
              <el-table-column prop="type" label="类型" width="120">
                <template #default="{ row }">
                  <el-tag :type="getLawTypeTag(row.type)">
                    {{ getLawTypeText(row.type) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="uploadTime" label="上传时间" width="180" />
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link @click="previewLaw(row)">预览</el-button>
                  <el-button type="danger" link @click="deleteLaw(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- 内容管理 -->
        <div v-if="activeMenu === 'content-manage'" class="admin-section">
          <h3 class="section-title">内容管理</h3>

          <!-- 内容管理标签页 -->
          <el-tabs v-model="contentActiveTab" type="border-card">
            <!-- 系统公告 Tab -->
            <el-tab-pane label="系统公告" name="announcement">
              <div class="tab-content">
                <!-- 发布公告表单 -->
                <div class="announcement-form">
                  <el-form :model="announcementForm" label-width="100px">
                    <el-form-item label="公告标题" required>
                      <el-input
                        v-model="announcementForm.title"
                        placeholder="请输入公告标题"
                        maxlength="100"
                        show-word-limit
                      />
                    </el-form-item>
                    <el-form-item label="公告类型">
                      <el-radio-group v-model="announcementForm.type">
                        <el-radio label="system">系统公告</el-radio>
                        <el-radio label="feature">功能更新</el-radio>
                        <el-radio label="maintenance">维护通知</el-radio>
                        <el-radio label="other">其他</el-radio>
                      </el-radio-group>
                    </el-form-item>
                    <el-form-item label="公告内容" required>
                      <el-input
                        v-model="announcementForm.content"
                        type="textarea"
                        :rows="6"
                        placeholder="请输入公告内容，支持 Markdown 格式"
                        maxlength="2000"
                        show-word-limit
                      />
                    </el-form-item>
                    <el-form-item label="发布时间">
                      <el-radio-group v-model="announcementForm.publishType">
                        <el-radio label="immediate">立即发布</el-radio>
                        <el-radio label="scheduled">定时发布</el-radio>
                      </el-radio-group>
                    </el-form-item>
                    <el-form-item v-if="announcementForm.publishType === 'scheduled'" label="定时时间">
                      <el-date-picker
                        v-model="announcementForm.publishTime"
                        type="datetime"
                        placeholder="选择发布时间"
                        style="width: 100%"
                      />
                    </el-form-item>
                    <el-form-item label="置顶显示">
                      <el-switch v-model="announcementForm.isTop" />
                    </el-form-item>
                    <el-form-item>
                      <el-button type="primary" :loading="publishing" @click="publishAnnouncement">
                        <el-icon><Promotion /></el-icon>
                        <span>{{ isEditingNotice ? '保存修改' : '发布公告' }}</span>
                      </el-button>
                      <el-button @click="resetAnnouncementForm">{{ isEditingNotice ? '取消编辑' : '重置' }}</el-button>
                    </el-form-item>
                  </el-form>
                </div>

                <!-- 公告列表 -->
                <div class="announcement-list">
                  <h4>历史公告</h4>
                  <el-table :data="announcements" style="width: 100%" v-loading="loadingAnnouncements">
                    <el-table-column prop="title" label="标题" min-width="200">
                      <template #default="{ row }">
                        <div class="announcement-title">
                          <el-tag v-if="row.isTop" type="danger" size="small" effect="dark">置顶</el-tag>
                          <span>{{ row.title }}</span>
                        </div>
                      </template>
                    </el-table-column>
                    <el-table-column prop="type" label="类型" width="100">
                      <template #default="{ row }">
                        <el-tag :type="getAnnouncementTypeTag(row.type)">
                          {{ getAnnouncementTypeText(row.type) }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="status" label="状态" width="100">
                      <template #default="{ row }">
                        <el-tag :type="row.status === 'published' ? 'success' : 'info'">
                          {{ row.status === 'published' ? '已发布' : '待发布' }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="publishTime" label="发布时间" width="180" />
                    <el-table-column prop="author" label="发布人" width="120" />
                    <el-table-column label="操作" width="200" fixed="right">
                      <template #default="{ row }">
                        <el-button type="primary" link @click="editAnnouncement(row)">编辑</el-button>
                        <el-button type="success" link @click="toggleTop(row)">
                          {{ row.isTop ? '取消置顶' : '置顶' }}
                        </el-button>
                        <el-button type="danger" link @click="handleDeleteAnnouncement(row)">删除</el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </el-tab-pane>

            <!-- 系统文档 Tab -->
            <el-tab-pane label="系统文档" name="system-docs">
              <div class="tab-content">
                <div class="upload-area">
                  <el-upload
                    drag
                    action="/api/admin/system-docs/upload"
                    :auto-upload="false"
                    :on-change="handleSystemDocChange"
                    :on-remove="handleSystemDocRemove"
                    :file-list="systemDocFileList"
                    accept=".pdf,.doc,.docx,.md,.txt"
                    multiple
                  >
                    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                    <div class="el-upload__text">
                      将文件拖到此处，或<em>点击上传</em>
                    </div>
                    <template #tip>
                      <div class="el-upload__tip">
                        支持 Word、Markdown 格式文件，单个文件不超过 50MB
                        <el-button type="primary" link size="small" @click="previewSystemExampleFile">
                          <el-icon><View /></el-icon>
                          示例文件
                        </el-button>
                        <div>(请务必按照示例文件格式上传)</div>
                      </div>
                    </template>
                  </el-upload>
                </div>

                <div class="upload-form">
                  <el-form :model="systemDocForm" label-width="100px">
                    <el-form-item label="文档分类" required>
                      <el-select
                        v-model="systemDocForm.category"
                        placeholder="请选择文档分类"
                        style="width: 100%"
                      >
                        <el-option label="用户手册" value="manual" />
                        <el-option label="操作指南" value="guide" />
                        <el-option label="常见问题" value="faq" />
                        <el-option label="系统说明" value="system" />
                        <el-option label="其他文档" value="other" />
                      </el-select>
                    </el-form-item>

                    <el-form-item label="文档标签">
                      <el-select
                        v-model="systemDocForm.tags"
                        multiple
                        filterable
                        allow-create
                        default-first-option
                        placeholder="请选择或输入标签"
                        style="width: 100%"
                      >
                        <el-option label="新手入门" value="beginner" />
                        <el-option label="高级功能" value="advanced" />
                        <el-option label="合同审查" value="review" />
                        <el-option label="法律知识" value="law" />
                        <el-option label="账号管理" value="account" />
                        <el-option label="故障排除" value="troubleshooting" />
                      </el-select>
                    </el-form-item>

                    <el-form-item label="文档说明">
                      <el-input
                        v-model="systemDocForm.description"
                        type="textarea"
                        :rows="3"
                        placeholder="请输入文档说明，帮助用户理解文档内容"
                      />
                    </el-form-item>
                  </el-form>
                </div>

                <div class="upload-actions">
                  <el-button type="primary" :loading="uploadingSystemDoc" @click="uploadSystemDocs">
                    <el-icon><Upload /></el-icon>
                    <span>开始上传</span>
                  </el-button>
                  <el-button @click="clearSystemDocFiles">清空列表</el-button>
                </div>

                <div class="uploaded-list">
                  <h4>已上传文档</h4>
                  <el-table :data="uploadedSystemDocs" style="width: 100%" v-loading="loadingSystemDocs">
                    <el-table-column prop="name" label="文档名称" min-width="200" />

                    <el-table-column prop="category" label="分类" width="120">
                      <template #default="{ row }">
                        <el-tag :type="getSystemDocCategoryTag(row.category)">
                          {{ getSystemDocCategoryText(row.category) }}
                        </el-tag>
                      </template>
                    </el-table-column>

                    <el-table-column prop="tags" label="标签" width="280">
                      <template #default="{ row }">
                        <div class="tag-list">
                          <el-tag
                            v-for="(tag, index) in row.tags"
                            :key="index"
                            size="small"
                            type="info"
                            class="tag-item"
                          >
                            {{ tag }}
                          </el-tag>
                        </div>
                      </template>
                    </el-table-column>

                    <el-table-column prop="uploadTime" label="上传时间" width="180" />

                    <el-table-column label="操作" width="150" fixed="right">
                      <template #default="{ row }">
                        <el-button type="primary" link @click="previewSystemDoc(row)">预览</el-button>
                        <el-button type="danger" link @click="deleteSystemDoc(row)">删除</el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>

        <!-- 用户管理 -->
        <div v-if="activeMenu === 'users'" class="admin-section">
          <h3 class="section-title">用户管理</h3>
          <div class="user-list">
            <el-table :data="users" style="width: 100%" v-loading="loadingUsers">
              <el-table-column prop="username" label="用户名" min-width="120" />
              <el-table-column prop="nickName" label="昵称" min-width="120" />
              <el-table-column prop="email" label="邮箱" min-width="180" />
              <el-table-column prop="phone" label="手机号" min-width="140" />
              <el-table-column prop="role" label="角色" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">
                    {{ row.role === 'admin' ? '管理员' : '普通用户' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
                    {{ row.status === 'active' ? '正常' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="createTime" label="注册时间" width="180" />
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link @click="editUser(row)">编辑</el-button>
                  <el-button type="warning" link @click="toggleUserStatus(row)">
                    {{ row.status === 'active' ? '禁用' : '启用' }}
                  </el-button>
                  <el-button type="danger" link @click="handleDeleteUser(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div class="pagination-wrapper">
              <el-pagination
                v-model:current-page="userPageNum"
                v-model:page-size="userPageSize"
                :page-sizes="[10, 20, 50]"
                :total="userTotal"
                layout="total, sizes, prev, pager, next"
                @size-change="loadUserList"
                @current-change="loadUserList"
              />
            </div>
          </div>
        </div>

        <!-- 编辑用户弹框 -->
        <el-dialog
          v-model="editUserDialogVisible"
          title="编辑用户"
          width="500px"
          :close-on-click-modal="false"
          @close="closeEditUserDialog"
        >
          <el-form
            ref="editUserFormRef"
            :model="editUserForm"
            :rules="editUserRules"
            label-width="80px"
          >
            <el-form-item label="用户名（账号登录）" prop="username">
              <el-input v-model="editUserForm.username" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="昵称" prop="nickName">
              <el-input v-model="editUserForm.nickName" placeholder="请输入昵称" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="editUserForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="editUserForm.phone" placeholder="请输入手机号" />
            </el-form-item>
            <el-form-item label="角色" prop="role">
              <el-select v-model="editUserForm.role" placeholder="请选择角色" style="width: 100%">
                <el-option label="管理员" value="admin" />
                <el-option label="普通用户" value="user" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <span class="dialog-footer">
              <el-button @click="closeEditUserDialog">取消</el-button>
              <el-button type="primary" :loading="submitting" @click="submitEditUser">确定</el-button>
            </span>
          </template>
        </el-dialog>

        <!-- 法律文档预览对话框 -->
        <el-dialog
          v-model="previewDialogVisible"
          :title="previewDocName"
          width="80%"
          :close-on-click-modal="false"
          destroy-on-close
        >
          <div class="preview-container">
            <!-- PDF 预览 -->
            <PdfPreview
              v-if="previewFileBlob && previewFileType === 'pdf'"
              :file-blob="previewFileBlob"
            />
            <!-- DOCX 预览 -->
            <DocxPreview
              v-else-if="previewFileBlob && (previewFileType === 'docx' || previewFileType === 'doc')"
              :file-blob="previewFileBlob"
            />
            <!-- TXT 预览 -->
            <TxtPreview
              v-else-if="previewFileBlob && (previewFileType === 'txt' || previewFileType === 'text')"
              :file-blob="previewFileBlob"
            />
            <!-- Markdown 预览 -->
            <TxtPreview
              v-else-if="previewFileBlob && (previewFileType === 'md' || previewFileType === 'markdown')"
              :file-blob="previewFileBlob"
            />
            <!-- 加载中 -->
            <div v-else-if="!previewFileBlob" class="preview-loading">
              <el-icon class="loading-icon"><Loading /></el-icon>
              <span>正在加载文档...</span>
            </div>
            <!-- 不支持的类型 -->
            <div v-else class="preview-loading">
              <el-icon class="loading-icon"><Document /></el-icon>
              <span>暂不支持该文件类型的预览: {{ previewFileType }}</span>
            </div>
          </div>
        </el-dialog>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserList, updateUser, updateUserStatus, deleteUser, uploadLawDocument, getLawDocumentList, deleteLawDocument, getLawDocumentFile, publishNotice, getNoticeList, editNotice, deleteNotice, toggleNoticeTop, uploadSystemDocument, getSystemDocList, deleteSystemDocument, getSystemDocumentFile } from '@/api/admin'

import { SecureStorage } from '@/utils/secureStorage'
import PdfPreview from '@/components/preview/PdfPreview.vue'
import DocxPreview from '@/components/preview/DocxPreview.vue'
import TxtPreview from '@/components/preview/TxtPreview.vue'
import { Loading, Document } from '@element-plus/icons-vue'

// 编辑模式状态
const isEditingNotice = ref(false)
const editingNoticeId = ref(null)

// 预览对话框状态
const previewDialogVisible = ref(false)
const previewDocName = ref('')
const previewFileBlob = ref(null)
const previewFileType = ref('')

// 当前选中的菜单，从 localStorage 读取
const activeMenu = ref(localStorage.getItem('admin_active_menu') || 'law-upload')
const contentActiveTab = ref('announcement')

// 监听菜单变化，保存到 localStorage
watch(activeMenu, (newVal) => {
  localStorage.setItem('admin_active_menu', newVal)
})

// 菜单项
const menuItems = [
  { key: 'law-upload', label: '法律文档上传', icon: 'Document' },
  { key: 'content-manage', label: '内容管理', icon: 'Collection' },
  { key: 'users', label: '用户管理', icon: 'User' }
]

// ========== 法律文档上传 ==========
const lawFileList = ref([])
const uploading = ref(false)
const lawForm = reactive({
  type: 'law',
  effectiveDate: null,
  description: ''
})

const uploadedLaws = ref([])
const loadingLaws = ref(false)

// 加载法律文档列表
async function loadLawDocumentList() {
  loadingLaws.value = true
  try {
    const res = await getLawDocumentList()
    if (res.code === 200) {
      uploadedLaws.value = res.data.map(doc => ({
        id: doc.id,
        name: doc.name,
        type: doc.type?.toLowerCase() || 'other',
        uploadTime: doc.createAt ? new Date(doc.createAt).toLocaleString() : '-'
      }))
    }
  } catch (error) {
    ElMessage.error('获取法律文档列表失败')
  } finally {
    loadingLaws.value = false
  }
}

function handleLawFileChange(file, fileList) {
  lawFileList.value = fileList
}

function handleLawFileRemove(file, fileList) {
  lawFileList.value = fileList
}

function clearLawFiles() {
  lawFileList.value = []
  lawForm.type = 'law'
  lawForm.effectiveDate = null
  lawForm.description = ''
}

async function uploadLawFiles() {
  if (lawFileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  uploading.value = true
  try {
    // 逐个上传文件
    for (const file of lawFileList.value) {
      const formData = new FormData()
      formData.append('file', file.raw)
      formData.append('type', lawForm.type)
      if (lawForm.effectiveDate) {
        formData.append('effectiveDate', lawForm.effectiveDate.toISOString().split('T')[0])
      }
      if (lawForm.description) {
        formData.append('description', lawForm.description)
      }

      const res = await uploadLawDocument(formData)
      if (res.code === 200) {
        ElMessage.success(`文件 "${file.name}" 上传成功`)
      } else {
        ElMessage.error(`文件 "${file.name}" 上传失败: ${res.message}`)
      }
    }

    clearLawFiles()
    loadLawDocumentList() // 刷新列表
  } catch (error) {
    ElMessage.error('上传失败: ' + (error.message || '未知错误'))
  } finally {
    uploading.value = false
  }
}

function getLawTypeTag(type) {
  const map = {
    law: 'danger',
    interpretation: 'warning',
    template: 'success',
    other: 'info'
  }
  return map[type] || 'info'
}

function getLawTypeText(type) {
  const map = {
    law: '法律法规',
    interpretation: '司法解释',
    template: '合同范本',
    other: '其他'
  }
  return map[type] || '其他'
}

async function previewLaw(row) {
  previewDialogVisible.value = true
  previewDocName.value = row.name
  previewFileBlob.value = null
  // 从文件名中提取文件类型
  const fileExt = row.name.split('.').pop().toLowerCase()
  previewFileType.value = fileExt
  console.log('预览文件类型:', fileExt)

  try {
    // 使用 fetch API 直接获取文件
    const token = SecureStorage.getToken()
    console.log('Token:', token ? '存在' : '不存在')
    const response = await fetch(`/api/admin/law/${row.id}/file`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const blob = await response.blob()
    console.log('获取到文件blob:', blob.size, 'bytes')
    previewFileBlob.value = blob
  } catch (error) {
    console.error('加载文档失败:', error)
    ElMessage.error('加载文档失败: ' + (error.message || '未知错误'))
    previewDialogVisible.value = false
  }
}

async function deleteLaw(row) {
  try {
    await ElMessageBox.confirm(`确定要删除文档 "${row.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    const res = await deleteLawDocument(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadLawDocumentList() // 刷新列表
    } else {
      ElMessage.error('删除失败: ' + res.message)
    }
  } catch {
    // 取消删除
  }
}

// ========== 系统文档上传 ==========
const systemDocFileList = ref([])
const uploadingSystemDoc = ref(false)
const systemDocForm = reactive({
  category: 'manual',
  tags: [],
  description: ''
})

const uploadedSystemDocs = ref([])
const loadingSystemDocs = ref(false)

// 加载系统文档列表
async function loadSystemDocList() {
  loadingSystemDocs.value = true
  try {
    const res = await getSystemDocList()
    if (res.code === 200) {
      uploadedSystemDocs.value = res.data.map(doc => ({
        id: doc.id,
        name: doc.name,
        category: doc.category?.toLowerCase() || 'other',
        tags: parseTags(doc.tags),
        uploadTime: doc.createAt ? new Date(doc.createAt).toLocaleString() : '-'
      }))
    }
  } catch (error) {
    ElMessage.error('获取系统文档列表失败')
  } finally {
    loadingSystemDocs.value = false
  }
}

function handleSystemDocChange(file, fileList) {
  systemDocFileList.value = fileList
}

function handleSystemDocRemove(file, fileList) {
  systemDocFileList.value = fileList
}

function clearSystemDocFiles() {
  systemDocFileList.value = []
  systemDocForm.category = 'manual'
  systemDocForm.tags = []
  systemDocForm.description = ''
}

async function uploadSystemDocs() {
  if (systemDocFileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  uploadingSystemDoc.value = true
  try {
    for (const file of systemDocFileList.value) {
      const formData = new FormData()
      formData.append('file', file.raw)
      formData.append('category', systemDocForm.category)
      formData.append('tags', JSON.stringify(systemDocForm.tags))
      if (systemDocForm.description) {
        formData.append('description', systemDocForm.description)
      }

      const res = await uploadSystemDocument(formData)
      if (res.code === 200) {
        ElMessage.success(`文件 "${file.name}" 上传成功`)
      } else {
        ElMessage.error(`文件 "${file.name}" 上传失败: ${res.message}`)
      }
    }

    clearSystemDocFiles()
    loadSystemDocList()
  } catch (error) {
    ElMessage.error('上传失败: ' + (error.message || '未知错误'))
  } finally {
    uploadingSystemDoc.value = false
  }
}

function getSystemDocCategoryTag(category) {
  const map = {
    manual: 'primary',
    guide: 'success',
    faq: 'warning',
    system: 'info',
    other: 'info'
  }
  return map[category] || 'info'
}

function getSystemDocCategoryText(category) {
  const map = {
    manual: '用户手册',
    guide: '操作指南',
    faq: '常见问题',
    system: '系统说明',
    other: '其他文档'
  }
  return map[category] || '其他'
}

function parseTags(tags) {
  if (!tags || !Array.isArray(tags) || tags.length === 0) {
    return []
  }
  const tagMap = {
    beginner: '新手入门',
    advanced: '高级功能',
    review: '合同审查',
    law: '法律知识',
    account: '账号管理',
    troubleshooting: '故障排除'
  }
  return tags.map(tag => {
    const cleanTag = tag.replace(/[\[\]"]/g, '').trim()
    return tagMap[cleanTag] || cleanTag
  })
}

async function previewSystemDoc(row) {
  previewDialogVisible.value = true
  previewDocName.value = row.name
  previewFileBlob.value = null
  const fileExt = row.name.split('.').pop().toLowerCase()
  previewFileType.value = fileExt

  try {
    const token = SecureStorage.getToken()
    const response = await fetch(`/api/admin/system-docs/${row.id}/file`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const blob = await response.blob()
    previewFileBlob.value = blob
  } catch (error) {
    ElMessage.error('加载文档失败: ' + (error.message || '未知错误'))
    previewDialogVisible.value = false
  }
}

async function deleteSystemDoc(row) {
  try {
    await ElMessageBox.confirm(`确定要删除文档 "${row.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    const res = await deleteSystemDocument(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadSystemDocList()
    } else {
      ElMessage.error('删除失败: ' + res.message)
    }
  } catch {
    // 取消删除
  }
}

/**
 * 预览示例文件
 */
async function previewExampleFile() {
  previewDialogVisible.value = true
  previewDocName.value = '示例文件'
  previewFileBlob.value = null

  try {
    const token = SecureStorage.getToken()
    const response = await fetch('/api/admin/law/0/file', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const blob = await response.blob()
    
    // 从 Content-Disposition 头中获取文件名
    const contentDisposition = response.headers.get('Content-Disposition')
    let fileExt = 'pdf' // 默认类型
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (filenameMatch) {
        const filename = decodeURIComponent(filenameMatch[1].replace(/['"]/g, ''))
        fileExt = filename.split('.').pop().toLowerCase()
      }
    }
    
    // 如果没有从文件名获取到类型，尝试从 blob type 判断
    if (fileExt === 'pdf' && blob.type) {
      if (blob.type.includes('markdown') || blob.type.includes('text/markdown')) {
        fileExt = 'md'
      } else if (blob.type.includes('text/plain')) {
        fileExt = 'txt'
      } else if (blob.type.includes('word')) {
        fileExt = 'docx'
      }
    }
    
    previewFileType.value = fileExt
    previewFileBlob.value = blob
  } catch (error) {
    ElMessage.error('加载示例文件失败: ' + (error.message || '未知错误'))
    previewDialogVisible.value = false
  }
}

/**
 * 预览系统文档示例文件
 */
async function previewSystemExampleFile() {
  previewDialogVisible.value = true
  previewDocName.value = '系统文档示例文件'
  previewFileBlob.value = null
  previewFileType.value = ''

  try {
    const token = SecureStorage.getToken()
    const response = await fetch('/api/admin/system-docs/0/file', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const blob = await response.blob()

    // 从 Content-Disposition 头中获取文件名
    const contentDisposition = response.headers.get('Content-Disposition')
    let fileExt = ''

    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (filenameMatch) {
        const filename = decodeURIComponent(filenameMatch[1].replace(/['"]/g, ''))
        fileExt = filename.split('.').pop().toLowerCase()
      }
    }

    // 如果没有从文件名获取到类型，尝试从 blob type 判断
    if (!fileExt && blob.type) {
      if (blob.type.includes('markdown') || blob.type.includes('text/markdown')) {
        fileExt = 'md'
      } else if (blob.type.includes('word') || blob.type.includes('document')) {
        fileExt = 'docx'
      } else if (blob.type.includes('pdf')) {
        fileExt = 'pdf'
      } else if (blob.type.includes('text')) {
        fileExt = 'txt'
      }
    }

    // 必须先设置 fileType，再设置 blob，避免组件渲染时类型不匹配
    previewFileType.value = fileExt || 'docx'
    await nextTick()
    previewFileBlob.value = blob
  } catch (error) {
    ElMessage.error('加载示例文件失败: ' + (error.message || '未知错误'))
    previewDialogVisible.value = false
  }
}

// ========== 系统公告发布 ==========
const publishing = ref(false)
const announcementForm = reactive({
  title: '',
  type: 'system',
  content: '',
  publishType: 'immediate',
  publishTime: null,
  isTop: false
})

const announcements = ref([])
const loadingAnnouncements = ref(false)

// 加载公告列表
async function loadNoticeList() {
  loadingAnnouncements.value = true
  try {
    const res = await getNoticeList()
    if (res.code === 200) {
      announcements.value = res.data.map(notice => ({
        id: notice.id,
        title: notice.title,
        type: notice.type?.toLowerCase() || 'other',
        content: notice.content || '',
        status: notice.status?.toLowerCase() === 'published' ? 'published' : 'pending',
        publishTime: notice.publishTime ? new Date(notice.publishTime).toLocaleString() : (notice.createdAt ? new Date(notice.createdAt).toLocaleString() : '-'),
        author: '系统管理员',
        isTop: notice.isTop || false
      }))
    }
  } catch (error) {
    ElMessage.error('获取公告列表失败')
  } finally {
    loadingAnnouncements.value = false
  }
}

async function publishAnnouncement() {
  if (!announcementForm.title.trim()) {
    ElMessage.warning('请输入公告标题')
    return
  }
  if (!announcementForm.content.trim()) {
    ElMessage.warning('请输入公告内容')
    return
  }

  publishing.value = true
  try {
    const data = {
      title: announcementForm.title,
      type: announcementForm.type.toLowerCase(),
      content: announcementForm.content,
      publishType: announcementForm.publishType.toLowerCase(),
      publishTime: announcementForm.publishType === 'scheduled' ? announcementForm.publishTime : null,
      isTop: announcementForm.isTop
    }

    let res
    if (isEditingNotice.value && editingNoticeId.value) {
      // 编辑模式：调用编辑API
      res = await editNotice(editingNoticeId.value, data)
      if (res.code === 200) {
        ElMessage.success('公告编辑成功')
      } else {
        ElMessage.error('编辑失败: ' + res.message)
      }
    } else {
      // 新增模式：调用发布API
      res = await publishNotice(data)
      if (res.code === 200) {
        ElMessage.success('公告发布成功')
      } else {
        ElMessage.error('发布失败: ' + res.message)
      }
    }

    if (res.code === 200) {
      resetAnnouncementForm()
      loadNoticeList() // 刷新列表
    }
  } catch (error) {
    ElMessage.error('操作失败: ' + (error.message || '未知错误'))
  } finally {
    publishing.value = false
  }
}

function resetAnnouncementForm() {
  announcementForm.title = ''
  announcementForm.type = 'system'
  announcementForm.content = ''
  announcementForm.publishType = 'immediate'
  announcementForm.publishTime = null
  announcementForm.isTop = false
  // 重置编辑模式
  isEditingNotice.value = false
  editingNoticeId.value = null
}

function getAnnouncementTypeTag(type) {
  const map = {
    system: 'primary',
    feature: 'success',
    maintenance: 'warning',
    other: 'info'
  }
  return map[type] || 'info'
}

function getAnnouncementTypeText(type) {
  const map = {
    system: '系统公告',
    feature: '功能更新',
    maintenance: '维护通知',
    other: '其他'
  }
  return map[type] || '其他'
}

function editAnnouncement(row) {
  // 填充表单进行编辑
  announcementForm.title = row.title
  announcementForm.type = row.type
  announcementForm.content = row.content || ''
  announcementForm.isTop = row.isTop
  // 设置编辑模式
  isEditingNotice.value = true
  editingNoticeId.value = row.id
  // 滚动到表单区域
  document.querySelector('.announcement-form')?.scrollIntoView({ behavior: 'smooth' })
  ElMessage.info(`正在编辑公告: ${row.title}，请修改后点击发布`)
}

async function toggleTop(row) {
  try {
    const res = await toggleNoticeTop(row.id, !row.isTop)
    if (res.code === 200) {
      row.isTop = !row.isTop
      ElMessage.success(row.isTop ? '已置顶' : '已取消置顶')
      loadNoticeList() // 刷新列表
    } else {
      ElMessage.error('操作失败: ' + res.message)
    }
  } catch (error) {
    ElMessage.error('操作失败: ' + (error.message || '未知错误'))
  }
}

async function handleDeleteAnnouncement(row) {
  try {
    await ElMessageBox.confirm(`确定要删除公告 "${row.title}" 吗？`, '确认删除', {
      type: 'warning'
    })
    const res = await deleteNotice(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadNoticeList() // 刷新列表
    } else {
      ElMessage.error('删除失败: ' + res.message)
    }
  } catch {
    // 取消删除
  }
}

// ========== 用户管理 ==========
const users = ref([])
const userPageNum = ref(1)
const userPageSize = ref(10)
const userTotal = ref(0)
const loadingUsers = ref(false)

// 加载用户列表
async function loadUserList() {
  loadingUsers.value = true
  try {
    const res = await getUserList({
      pageNum: userPageNum.value,
      pageSize: userPageSize.value
    })
    if (res.code === 200) {
      users.value = res.data.records.map(user => ({
        ...user,
        role: user.role?.toLowerCase() === 'admin' ? 'admin' : 'user',
        // status: 0=禁用, 1=启用
        status: user.status === 1 ? 'active' : 'disabled',
        createTime: user.createdAt ? new Date(user.createdAt).toLocaleString() : '-'
      }))
      userTotal.value = res.data.total
    }
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loadingUsers.value = false
  }
}

// 编辑用户弹框
const editUserDialogVisible = ref(false)
const editUserForm = reactive({
  id: null,
  username: '',
  nickName: '',
  email: '',
  phone: '',
  role: ''
})
const editUserFormRef = ref(null)
const submitting = ref(false)

const editUserRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应为3-20个字符', trigger: 'blur' }
  ],
  nickName: [
    { max: 20, message: '昵称最多20个字符', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

function editUser(row) {
  editUserForm.id = row.id
  editUserForm.username = row.username
  editUserForm.nickName = row.nickName
  editUserForm.email = row.email
  editUserForm.phone = row.phone || ''
  editUserForm.role = row.role
  editUserDialogVisible.value = true
}

function closeEditUserDialog() {
  editUserDialogVisible.value = false
  editUserFormRef.value?.resetFields()
}

async function submitEditUser() {
  if (!editUserFormRef.value) return

  await editUserFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const res = await updateUser(editUserForm.id, {
          username: editUserForm.username,
          nickName: editUserForm.nickName,
          email: editUserForm.email,
          phone: editUserForm.phone,
          role: editUserForm.role
        })
        if (res.code === 200) {
          ElMessage.success('用户编辑成功')
          closeEditUserDialog()
          loadUserList()
        }
      } catch (error) {
        ElMessage.error('用户编辑失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

async function toggleUserStatus(row) {
  const newStatus = row.status === 'active' ? 'DISABLED' : 'ENABLED'
  const action = row.status === 'active' ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定要${action}用户 "${row.username}" 吗？`, '确认', {
      type: 'warning'
    })
    const res = await updateUserStatus(row.id, newStatus)
    if (res.code === 200) {
      row.status = newStatus === 'ENABLED' ? 'active' : 'disabled'
      ElMessage.success(`${action}成功`)
      // 返回 0 表示禁用，1 表示启用
      return newStatus === 'ENABLED' ? 1 : 0
    }
  } catch {
    // 取消
  }
  return null
}

async function handleDeleteUser(row) {
  try {
    await ElMessageBox.confirm(`确定要删除用户 "${row.username}" 吗？此操作不可恢复！`, '确认删除', {
      type: 'danger'
    })
    const res = await deleteUser(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadUserList()
    }
  } catch {
    // 取消删除
  }
}

// 监听菜单切换，加载对应数据
watch(activeMenu, (newVal) => {
  if (newVal === 'users') {
    loadUserList()
  } else if (newVal === 'law-upload') {
    loadLawDocumentList()
  } else if (newVal === 'content-manage') {
    loadNoticeList()
    loadSystemDocList()
  }
}, { immediate: true })
</script>

<style scoped lang="scss">
.admin-page {
  min-height: calc(100vh - 64px);
  background: $bg-secondary;
}

.page-header {
  padding: 24px;
  background: white;
  border-bottom: 1px solid $border-color;

  .page-title {
    font-size: $font-size-xl;
    font-weight: 600;
    color: $text-primary;
    margin: 0;
  }
}

.admin-content {
  display: flex;
  padding: 24px;
  gap: 24px;
}

.admin-sidebar {
  width: 200px;
  background: white;
  border-radius: $radius-lg;
  padding: 16px 0;
  box-shadow: $shadow-sm;
  flex-shrink: 0;

  .menu-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 20px;
    cursor: pointer;
    transition: all $transition-fast;
    color: $text-secondary;

    &:hover {
      background: $bg-secondary;
      color: $primary-color;
    }

    &.active {
      background: rgba($primary-color, 0.1);
      color: $primary-color;
      border-right: 3px solid $primary-color;
    }

    .el-icon {
      font-size: 18px;
    }
  }
}

.admin-main {
  flex: 1;
  background: white;
  border-radius: $radius-lg;
  padding: 24px;
  box-shadow: $shadow-sm;
}

.admin-section {
  .section-title {
    font-size: $font-size-lg;
    font-weight: 600;
    color: $text-primary;
    margin: 0 0 24px 0;
    padding-bottom: 16px;
    border-bottom: 1px solid $border-color;
  }
}

// 法律文档上传
.upload-area {
  margin-bottom: 24px;
}

.upload-form {
  max-width: 600px;
  margin-bottom: 24px;
}

.upload-actions {
  margin-bottom: 32px;
}

.uploaded-list {
  h4 {
    font-size: $font-size-base;
    font-weight: 600;
    color: $text-primary;
    margin: 0 0 16px 0;
  }

  .tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;

    .tag-item {
      margin: 0;
    }
  }
}

// 公告发布
.announcement-form {
  max-width: 800px;
  margin-bottom: 32px;
}

.announcement-list {
  h4 {
    font-size: $font-size-base;
    font-weight: 600;
    color: $text-primary;
    margin: 0 0 16px 0;
  }
}

.announcement-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

// 内容管理标签页
:deep(.el-tabs--border-card) {
  border-radius: $radius-md;
  border: 1px solid $border-color;

  .el-tabs__header {
    background-color: $bg-secondary;
    border-bottom: 1px solid $border-color;
    border-radius: $radius-md $radius-md 0 0;

    .el-tabs__item {
      height: 44px;
      line-height: 44px;
      font-size: $font-size-base;
      color: $text-secondary;
      border-right: 1px solid $border-color;
      transition: all 0.3s ease;

      &:hover {
        color: $primary-color;
      }

      &.is-active {
        color: $primary-color;
        background-color: #fff;
        border-bottom-color: transparent;
      }
    }
  }

  .el-tabs__content {
    padding: 24px;
  }
}

.tab-content {
  .upload-area {
    margin-bottom: 24px;
  }

  .announcement-form {
    margin-bottom: 24px;
  }
}

// 日志
.log-filters {
  margin-bottom: 24px;
  padding: 16px;
  background: $bg-secondary;
  border-radius: $radius-md;
}

// 用户管理
.user-list {
  margin-top: 16px;
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

// 预览对话框样式
.preview-container {
  min-height: 400px;
  max-height: 70vh;
  overflow: auto;
}

.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: #909399;

  .loading-icon {
    font-size: 32px;
    margin-bottom: 16px;
    animation: rotating 2s linear infinite;
  }
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
