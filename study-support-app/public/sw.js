self.addEventListener('push', function(event) {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.message,
      icon: '/icon-192x192.png',
      badge: '/badge-72x72.png',
      data: data.metadata || {},
      actions: data.actions || [],
      vibrate: [200, 100, 200],
      requireInteraction: true,
    };

    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();

  if (event.action) {
    // アクションボタンがクリックされた場合の処理
    const action = event.action;
    const metadata = event.notification.data;

    // アクションに応じた処理を実装
    switch (action) {
      case 'open':
        if (metadata.url) {
          event.waitUntil(
            clients.openWindow(metadata.url)
          );
        }
        break;
      // 他のアクションの処理を追加
    }
  } else {
    // 通知自体がクリックされた場合
    const metadata = event.notification.data;
    if (metadata.url) {
      event.waitUntil(
        clients.openWindow(metadata.url)
      );
    }
  }
}); 