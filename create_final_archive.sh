#!/bin/bash

# 休講見逃し防止アプリ - 最終提出アーカイブ作成スクリプト
# 実行日: $(date '+%Y年%m月%d日 %H:%M:%S')

echo "============================================"
echo "休講見逃し防止アプリ - 最終提出アーカイブ作成"
echo "============================================"

# アーカイブディレクトリ作成
ARCHIVE_DIR="final_submission_$(date '+%Y%m%d_%H%M%S')"
mkdir -p "$ARCHIVE_DIR"

echo "✅ アーカイブディレクトリ作成: $ARCHIVE_DIR"

# 必要なファイルのコピー
echo "📁 重要ファイルをコピー中..."

# プロジェクトルート
cp README.md "$ARCHIVE_DIR/" 2>/dev/null || echo "⚠️ README.md not found"
cp LICENSE "$ARCHIVE_DIR/" 2>/dev/null || echo "⚠️ LICENSE not found"
cp LICENSE_JP "$ARCHIVE_DIR/" 2>/dev/null || echo "⚠️ LICENSE_JP not found"

# Unityプロジェクト（重要ファイルのみ）
mkdir -p "$ARCHIVE_DIR/Assets"
cp -r Assets/*.cs "$ARCHIVE_DIR/Assets/" 2>/dev/null
cp -r Assets/*.asmdef "$ARCHIVE_DIR/Assets/" 2>/dev/null
cp -r Assets/Tests "$ARCHIVE_DIR/Assets/" 2>/dev/null || echo "⚠️ Tests directory not found"
cp -r Assets/Res "$ARCHIVE_DIR/Assets/" 2>/dev/null || echo "⚠️ Res directory not found"

# プロジェクト設定
mkdir -p "$ARCHIVE_DIR/ProjectSettings"
cp ProjectSettings/ProjectSettings.asset "$ARCHIVE_DIR/ProjectSettings/" 2>/dev/null
cp ProjectSettings/ProjectVersion.txt "$ARCHIVE_DIR/ProjectSettings/" 2>/dev/null

# パッケージ設定
mkdir -p "$ARCHIVE_DIR/Packages"
cp Packages/manifest.json "$ARCHIVE_DIR/Packages/" 2>/dev/null
cp Packages/packages-lock.json "$ARCHIVE_DIR/Packages/" 2>/dev/null

# サーバーサイド
mkdir -p "$ARCHIVE_DIR/klms-cancel-fetcher"
cp klms-cancel-fetcher/*.py "$ARCHIVE_DIR/klms-cancel-fetcher/" 2>/dev/null
cp klms-cancel-fetcher/*.txt "$ARCHIVE_DIR/klms-cancel-fetcher/" 2>/dev/null
cp klms-cancel-fetcher/*.md "$ARCHIVE_DIR/klms-cancel-fetcher/" 2>/dev/null
cp klms-cancel-fetcher/.env.example "$ARCHIVE_DIR/klms-cancel-fetcher/" 2>/dev/null

# ドキュメント
mkdir -p "$ARCHIVE_DIR/docs"
cp -r docs/* "$ARCHIVE_DIR/docs/" 2>/dev/null

echo "✅ ファイルコピー完了"

# ファイル数とサイズ確認
echo ""
echo "📊 アーカイブ統計:"
echo "ファイル数: $(find "$ARCHIVE_DIR" -type f | wc -l)"
echo "ディレクトリ数: $(find "$ARCHIVE_DIR" -type d | wc -l)"
echo "合計サイズ: $(du -sh "$ARCHIVE_DIR" | cut -f1)"

# ZIP圧縮
echo ""
echo "🗜️  ZIP圧縮中..."
zip -r "${ARCHIVE_DIR}.zip" "$ARCHIVE_DIR" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ アーカイブ作成完了: ${ARCHIVE_DIR}.zip"
    echo "📁 ZIP サイズ: $(ls -lh "${ARCHIVE_DIR}.zip" | awk '{print $5}')"
else
    echo "❌ ZIP圧縮に失敗しました"
    exit 1
fi

# チェックサム生成
echo ""
echo "🔐 チェックサム生成中..."
if command -v shasum > /dev/null 2>&1; then
    shasum -a 256 "${ARCHIVE_DIR}.zip" > "${ARCHIVE_DIR}.zip.sha256"
    echo "✅ SHA256チェックサム: ${ARCHIVE_DIR}.zip.sha256"
elif command -v sha256sum > /dev/null 2>&1; then
    sha256sum "${ARCHIVE_DIR}.zip" > "${ARCHIVE_DIR}.zip.sha256"
    echo "✅ SHA256チェックサム: ${ARCHIVE_DIR}.zip.sha256"
else
    echo "⚠️ SHA256コマンドが見つかりません"
fi

# 最終確認
echo ""
echo "============================================"
echo "🎉 最終提出アーカイブ作成完了！"
echo "============================================"
echo "📦 アーカイブファイル: ${ARCHIVE_DIR}.zip"
echo "📋 チェックサムファイル: ${ARCHIVE_DIR}.zip.sha256"
echo "📁 作業ディレクトリ: $ARCHIVE_DIR"
echo ""
echo "提出前チェックリスト:"
echo "□ アーカイブファイルが正常に作成されている"
echo "□ 重要なソースコードが含まれている"
echo "□ ドキュメントが含まれている"  
echo "□ チェックサムファイルが生成されている"
echo ""
echo "🚀 準備完了です！"