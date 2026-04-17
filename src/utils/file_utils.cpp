#include "file_utils.h"
#include <QFile>
#include <QDir>
#include <QFileInfo>
#include <QDebug>

namespace metatag {

bool FileUtils::safeMove(const QString& src, const QString& dst)
{
    if (src.isEmpty() || dst.isEmpty())
        return false;
    
    QFile srcFile(src);
    if (!srcFile.exists())
        return false;
    
    // Ensure destination directory exists
    QFileInfo dstInfo(dst);
    QDir dstDir = dstInfo.dir();
    if (!dstDir.exists() && !dstDir.mkpath("."))
        return false;
    
    // Remove destination if exists
    if (QFile::exists(dst) && !QFile::remove(dst))
        return false;
    
    return srcFile.rename(dst);
}

bool FileUtils::safeCopy(const QString& src, const QString& dst)
{
    if (src.isEmpty() || dst.isEmpty())
        return false;
    
    QFile srcFile(src);
    if (!srcFile.exists())
        return false;
    
    QFileInfo dstInfo(dst);
    QDir dstDir = dstInfo.dir();
    if (!dstDir.exists() && !dstDir.mkpath("."))
        return false;
    
    if (QFile::exists(dst) && !QFile::remove(dst))
        return false;
    
    return srcFile.copy(dst);
}

bool FileUtils::safeDelete(const QString& path)
{
    if (path.isEmpty())
        return false;
    
    QFile file(path);
    if (!file.exists())
        return true; // nothing to delete
    
    return file.remove();
}

QVector<QString> FileUtils::findAudioFiles(const QString& directory)
{
    QVector<QString> result;
    QDir rootDir(directory);
    if (!rootDir.exists())
        return result;
    
    // Supported audio extensions
    QStringList filters;
    filters << "*.mp3" << "*.flac" << "*.wav" << "*.aiff" << "*.ogg" << "*.m4a" << "*.mp4"
            << "*.oga" << "*.spx" << "*.opus" << "*.wma" << "*.aac";
    
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
        
        // Get subdirectories to process later
        auto subdirs = currentDir.entryList(QDir::Dirs | QDir::NoDotAndDotDot);
        for (const auto& subdir : subdirs) {
            dirQueue.enqueue(QDir(currentDir.absoluteFilePath(subdir)));
        }
    }
    
    return result;
}

}