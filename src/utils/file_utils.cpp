#include "file_utils.h"
#include <QFile>
#include <QDir>
#include <QFileInfo>
#include <QQueue>
#include <QDebug>
#include <filesystem>

namespace metatag {

bool FileUtils::safeMove(const QString& src, const QString& dst)
{
    if (src.isEmpty() || dst.isEmpty())
        return false;

    std::error_code ec;
#if defined(_WIN32)
    std::filesystem::path srcPath(src.toStdU16String());
    std::filesystem::path dstPath(dst.toStdU16String());
#else
    std::filesystem::path srcPath(src.toStdString());
    std::filesystem::path dstPath(dst.toStdString());
#endif

    if (!std::filesystem::exists(srcPath, ec) || ec)
        return false;

    ec.clear();
    if (std::filesystem::exists(dstPath, ec) && !ec) {
        if (std::filesystem::equivalent(srcPath, dstPath, ec) && !ec)
            return true;
    }
    ec.clear();

    if (dstPath.has_parent_path()) {
        std::filesystem::create_directories(dstPath.parent_path(), ec);
        if (ec) return false;
    }
    ec.clear();

    std::filesystem::rename(srcPath, dstPath, ec);
    if (!ec)
        return true;

    // Cross-device fallback: copy with overwrite, then remove src
    ec.clear();
    std::filesystem::copy_file(srcPath, dstPath, std::filesystem::copy_options::overwrite_existing, ec);
    if (!ec) {
        std::filesystem::remove(srcPath, ec);
        return true;
    }
    return false;
}

bool FileUtils::safeCopy(const QString& src, const QString& dst)
{
    if (src.isEmpty() || dst.isEmpty())
        return false;

    std::error_code ec;
#if defined(_WIN32)
    std::filesystem::path srcPath(src.toStdU16String());
    std::filesystem::path dstPath(dst.toStdU16String());
#else
    std::filesystem::path srcPath(src.toStdString());
    std::filesystem::path dstPath(dst.toStdString());
#endif

    if (!std::filesystem::exists(srcPath, ec) || ec)
        return false;

    ec.clear();
    if (std::filesystem::exists(dstPath, ec) && !ec) {
        if (std::filesystem::equivalent(srcPath, dstPath, ec) && !ec)
            return true;
    }
    ec.clear();

    if (dstPath.has_parent_path()) {
        std::filesystem::create_directories(dstPath.parent_path(), ec);
        if (ec) return false;
    }
    ec.clear();

    std::filesystem::copy_file(srcPath, dstPath, std::filesystem::copy_options::overwrite_existing, ec);
    return !ec;
}

bool FileUtils::safeDelete(const QString& path)
{
    if (path.isEmpty())
        return false;

    std::error_code ec;
#if defined(_WIN32)
    std::filesystem::path p(path.toStdU16String());
#else
    std::filesystem::path p(path.toStdString());
#endif

    if (!std::filesystem::exists(p, ec) || ec)
        return true; // nothing to delete

    ec.clear();
    std::filesystem::remove(p, ec);
    if (!ec)
        return true;

    // Fallback to QFile::remove
    QFile file(path);
    if (!file.exists())
        return true;
    return file.remove();
}

#include <QSet>

QVector<QString> FileUtils::findAudioFiles(const QString& directory)
{
    QVector<QString> result;
    QDir rootDir(directory);
    if (!rootDir.exists())
        return result;
    
    // Supported audio extensions (including audiobook formats)
    QStringList filters;
    filters << "*.mp3" << "*.flac" << "*.wav" << "*.aiff" << "*.ogg" << "*.m4a" << "*.mp4"
            << "*.oga" << "*.spx" << "*.opus" << "*.wma" << "*.aac" << "*.m4b" << "*.m4p";
    
    QSet<QString> visitedDirs;
    QString rootCanon = rootDir.canonicalPath();
    if (!rootCanon.isEmpty()) {
        visitedDirs.insert(rootCanon);
    }

    // BFS queue of directories to process
    QQueue<QDir> dirQueue;
    dirQueue.enqueue(rootDir);
    
    while (!dirQueue.isEmpty()) {
        QDir currentDir = dirQueue.dequeue();
        
        // Get files in current directory
        auto entries = currentDir.entryList(filters, QDir::Files | QDir::Readable, QDir::Name);
        for (const auto& entry : entries) {
            result.append(currentDir.absoluteFilePath(entry));
        }
        
        // Get subdirectories to process later, tracking visited canonical paths to prevent symlink loops
        auto subdirs = currentDir.entryInfoList(QDir::Dirs | QDir::NoDotAndDotDot | QDir::Readable);
        for (const auto& info : subdirs) {
            QString canon = info.canonicalFilePath();
            if (!canon.isEmpty() && !visitedDirs.contains(canon)) {
                visitedDirs.insert(canon);
                dirQueue.enqueue(QDir(info.absoluteFilePath()));
            }
        }
    }
    
    return result;
}

}