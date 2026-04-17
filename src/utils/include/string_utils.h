#pragma once

#include <QString>

namespace metatag {

class StringUtils {
public:
    static QString toTitleCase(const QString& str);
    static QString toSentenceCase(const QString& str);
    static QString toUpper(const QString& str);
    static QString toLower(const QString& str);
};

}