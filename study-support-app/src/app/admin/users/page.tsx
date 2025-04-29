'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { AdminNavBar } from '@/components/common/AdminNavBar';
import { User, UserRole } from '@/types/user';
import { Plus, Search, Edit, Trash2 } from 'lucide-react';
import { 
  getUsers,
  getUserDetails,
  createUser,
  updateUser,
  deleteUser,
  UserCreatePayload,
  UserUpdatePayload,
  UserDetailsResponse
} from '@/services/adminService';
import { getRoles } from '@/services/roleService';
import { RoleRead } from '@/types/role';
import UserDetailsModal from '@/components/admin/users/UserDetailsModal';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import RoleManagementTab from '@/components/admin/roles/RoleManagementTab';
import PermissionManagementTab from '@/components/admin/permissions/PermissionManagementTab';

const AdminUsersPage = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [availableRoles, setAvailableRoles] = useState<RoleRead[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true); // ローディング状態
  const [isLoadingRoles, setIsLoadingRoles] = useState(true); // ロール読み込み状態
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserDetailsResponse | null>(null);
  const [modalMode, setModalMode] = useState<'view' | 'edit' | 'add'>('view');

  // --- 日付フォーマット関数を追加 ---
  const formatDate = (dateString: string | undefined | null): string => {
    if (!dateString) return '-';
    try {
      // タイムゾーン情報がないISO文字列の場合、UTCとして解釈させるために 'Z' を追加
      const date = new Date(dateString.endsWith('Z') ? dateString : dateString + 'Z');

      // 日本語ロケール、年月日時分秒でフォーマット
      return new Intl.DateTimeFormat('ja-JP', {
        year: 'numeric', month: 'numeric', day: 'numeric',
        hour: 'numeric', minute: 'numeric', second: 'numeric',
        hour12: false, // 24時間表記
        timeZone: 'Asia/Tokyo' // タイムゾーンを日本時間に指定
      }).format(date); // 修正した date オブジェクトを使用
    } catch (e) {
      console.error("Date formatting error:", e);
      return dateString; // エラー時は元の文字列を返す
    }
  };
  // --- 日付フォーマット関数ここまで ---

  // モーダル用のユーザーデータ整形 (APIレスポンス -> User型)
  const mapResponseToUser = (res: UserDetailsResponse): User => ({
    id: res.id,
    name: res.name,
    email: res.email,
    role: res.role as UserRole, // APIレスポンスの role は日本語文字列のはず
    status: res.status as User['status'],
    createdAt: res.created_at, // created_at を使用
    lastLogin: res.last_login_at ?? undefined, // 直接 last_login_at を参照
  });

  // ユーザーリスト取得関数（再利用のため）
  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    try {
      const params: { search?: string; role?: string; status?: string } = {};
      if (searchTerm) params.search = searchTerm;
      if (filterRole !== 'all') params.role = filterRole;
      if (filterStatus !== 'all') params.status = filterStatus;

      const resp = await getUsers(params);
      // 1. APIレスポンス直後のログ
      console.log("API Response (raw):", resp);

      // --- 修正: API レスポンスのキーと型に合わせてマッピング --- 
      const mappedUsers = resp.users.map(u => ({
        id: u.id,
        name: u.name,
        email: u.email,
        role: u.role as UserRole, // バックエンドの role は日本語文字列
        status: u.status as User['status'],
        createdAt: u.created_at, // AdminUser 型に合わせて created_at を使用
        lastLogin: u.last_login_at ?? undefined, // 直接 last_login_at を参照
      }));
      // --------------------------------------------------------

      // 2. マッピング後のログ
      console.log("Mapped Users (before setState):", mappedUsers);

      setUsers(mappedUsers);
    } catch (error) {
      console.error('ユーザー取得エラー:', error);
    } finally {
      setIsLoading(false);
    }
  }, [searchTerm, filterRole, filterStatus]);

  // --- ロール一覧を取得する useEffect ---
  useEffect(() => {
    const fetchRoles = async () => {
      setIsLoadingRoles(true);
      try {
        const rolesData = await getRoles();
        // 必要に応じてソートやフィルタリング
        setAvailableRoles(rolesData.filter(role => role.is_active)); // アクティブなロールのみ表示する場合
        console.log("Fetched Roles:", rolesData);
      } catch (error) {
        console.error('ロール取得エラー:', error);
        // エラーハンドリング (例: トースト表示)
      } finally {
        setIsLoadingRoles(false);
      }
    };
    fetchRoles();
  }, []); // コンポーネントマウント時に1回だけ実行
  // --- ここまで ---

  useEffect(() => {
    fetchUsers();
  }, [searchTerm, filterRole, filterStatus, fetchUsers]);

  // ロール表示用のヘルパー (キーを日本語に変更)
  const roleDisplayMap: Record<string, string> = { // 型を Record<string, string> に変更
    "管理者": '管理者', // "admin" -> "管理者"
    "教員": '先生',   // "teacher" -> "教員" (表示名は「先生」のまま)
    "生徒": '生徒',   // "student" -> "生徒"
    // 必要に応じて他のロール（例：「システム」）のマッピングも追加
  };

  // ステータス表示用のヘルパー（Tailwindクラス含む）
  const statusDisplayMap: Record<User['status'], { text: string; className: string }> = {
    active: { text: 'アクティブ', className: 'bg-green-100 text-green-800' },
    inactive: { text: '非アクティブ', className: 'bg-gray-100 text-gray-800' },
    pending: { text: '保留中', className: 'bg-yellow-100 text-yellow-800' },
    unpaid: { text: '未決済', className: 'bg-orange-100 text-orange-800' },
  };

  // --- 各種ハンドラー ---
  const handleAddUser = () => {
    setSelectedUser(null);
    setModalMode('add');
    setIsModalOpen(true);
  };

  const handleViewDetails = async (userId: string) => {
    try {
      const userDetails = await getUserDetails(userId);
      setSelectedUser(userDetails);
      setModalMode('view');
      setIsModalOpen(true);
    } catch (error) {
      console.error('ユーザー詳細取得エラー:', error);
      alert('ユーザー情報の取得に失敗しました。');
    }
  };

  const handleEditUser = async (userId: string) => {
    try {
      const userDetails = await getUserDetails(userId);
      setSelectedUser(userDetails);
      setModalMode('edit');
      setIsModalOpen(true);
    } catch (error) {
      console.error('ユーザー編集情報取得エラー:', error);
      alert('ユーザー情報の取得に失敗しました。');
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedUser(null);
  };

  const handleSaveUser = async (userData: UserCreatePayload | UserUpdatePayload) => {
    try {
      if (modalMode === 'add') {
        if (!userData.password) {
          alert('新規作成時はパスワードが必須です。');
          return;
        }
        await createUser(userData as UserCreatePayload);
      } else if (modalMode === 'edit' && selectedUser) {
        await updateUser(selectedUser.id, userData as UserUpdatePayload);
      } else {
        console.error('不正なモードまたは選択されたユーザーなし');
        return;
      }
      // ユーザーリストを更新 (fetchUsers() を再実行するか、ローカルで更新)
      fetchUsers(); // 簡単な方法としてリスト全体を再取得
      handleCloseModal();
      alert(`ユーザー情報を${modalMode === 'add' ? '作成' : '更新'}しました。`);
    } catch (error) {
      console.error('ユーザー保存エラー:', error);
      alert(`ユーザー情報の${modalMode === 'add' ? '作成' : '更新'}に失敗しました。`);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm(`ユーザーID: ${userId} を削除してもよろしいですか？`)) return;
    try {
      await deleteUser(userId);
      setUsers(prev => prev.filter(u => u.id !== userId));
      alert(`ユーザーID: ${userId} を削除しました`);
    } catch (error) {
      console.error('ユーザー削除エラー:', error);
      alert('ユーザー削除に失敗しました。詳細はコンソールを確認してください。');
    }
  };

  return (
    <div>
      <AdminNavBar />
      <div className="min-h-screen bg-gray-50 p-6">
        <h1 className="text-2xl font-semibold text-gray-900 mb-6">管理ダッシュボード</h1>

        <Tabs defaultValue="users" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6">
            <TabsTrigger value="users">ユーザー管理</TabsTrigger>
            <TabsTrigger value="roles">ロール管理</TabsTrigger>
            <TabsTrigger value="permissions">権限管理</TabsTrigger>
          </TabsList>

          <TabsContent value="users">
            <div className="mb-6 flex flex-col sm:flex-row justify-between items-center">
              <h2 className="text-xl font-medium text-gray-800 mb-4 sm:mb-0">ユーザー一覧</h2>
              <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2 w-full sm:w-auto">
                <div className="relative">
                  <input
                    type="text"
                    placeholder="名前 or メールアドレスで検索..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent w-full sm:w-64"
                  />
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                </div>
                <select
                  value={filterRole}
                  onChange={(e) => setFilterRole(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isLoadingRoles}
                >
                  <option value="all">すべてのロール</option>
                  {availableRoles.map(role => (
                    <option key={role.id} value={role.name}>
                      {roleDisplayMap[role.name] || role.name}
                    </option>
                  ))}
                </select>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">すべてのステータス</option>
                  <option value="active">アクティブ</option>
                  <option value="inactive">非アクティブ</option>
                  <option value="pending">保留中</option>
                  <option value="unpaid">未決済</option>
                </select>
                <button
                  onClick={handleAddUser}
                  className="flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  <Plus className="h-5 w-5 mr-1" />
                  新規追加
                </button>
              </div>
            </div>

            <div className="bg-white shadow overflow-hidden rounded-md">
              {isLoading && (
                  <div className="text-center py-10">読み込み中...</div>
              )}
              {!isLoading && users.length === 0 && (
                 <div className="text-center py-10 text-gray-500">ユーザーが見つかりません。</div>
              )}
              {!isLoading && users.length > 0 && (
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">名前</th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">メールアドレス</th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ロール</th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ステータス</th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">登録日時</th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">最終ログイン</th>
                      <th scope="col" className="relative px-6 py-3">
                        <span className="sr-only">操作</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{user.name}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-500">{user.email}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                           {/* roleDisplayMap を使用して日本語表示 */}
                           <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                             {roleDisplayMap[user.role] || user.role} 
                           </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusDisplayMap[user.status]?.className || 'bg-gray-100 text-gray-800'}`}>
                            {statusDisplayMap[user.status]?.text || user.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(user.createdAt)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(user.lastLogin)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                           <button onClick={() => handleViewDetails(user.id)} className="text-indigo-600 hover:text-indigo-900" title="詳細表示">
                             <Search className="h-4 w-4 inline-block" />
                           </button>
                           <button onClick={() => handleEditUser(user.id)} className="text-green-600 hover:text-green-900" title="編集">
                             <Edit className="h-4 w-4 inline-block" />
                           </button>
                           <button onClick={() => handleDeleteUser(user.id)} className="text-red-600 hover:text-red-900" title="削除">
                             <Trash2 className="h-4 w-4 inline-block" />
                           </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {isModalOpen && (
              <UserDetailsModal
                isOpen={isModalOpen}
                onClose={handleCloseModal}
                user={selectedUser ? mapResponseToUser(selectedUser) : null}
                mode={modalMode}
                onSave={handleSaveUser}
                availableRoles={availableRoles}
                isLoadingRoles={isLoadingRoles}
              />
            )}
          </TabsContent>

          <TabsContent value="roles">
            <div className="bg-white shadow overflow-hidden rounded-md p-6">
              <RoleManagementTab />
            </div>
          </TabsContent>

          <TabsContent value="permissions">
            <div className="bg-white shadow overflow-hidden rounded-md p-6">
              <PermissionManagementTab />
            </div>
          </TabsContent>

        </Tabs>
      </div>
    </div>
  );
};

export default AdminUsersPage; 