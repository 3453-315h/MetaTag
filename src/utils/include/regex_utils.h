#pragma once

#include <QString>
#include <QVector>

namespace metatag {

class RegexUtils {
public:
    static QVector<QString> findMatches(const QString& pattern, const QString& text);
    static QString replaceMatches(const QString& pattern, const QString& replacement, const QString& text);
};

}