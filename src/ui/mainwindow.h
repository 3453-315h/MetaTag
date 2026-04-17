#pragma once

#include <QMainWindow>
#include <QString>
#include <QVector>
#include "track.h"

class QListWidget;
class QLineEdit;

class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void openFiles();
    void saveTags();
    void updateSelectedTrack();
    void artistChanged(const QString& text);
    void albumChanged(const QString& text);
    void titleChanged(const QString& text);

private:
    void setupUI();
    void loadTrack(int index);

    QListWidget *m_fileList;
    QLineEdit *m_artistEdit;
    QLineEdit *m_albumEdit;
    QLineEdit *m_titleEdit;
    QVector<metatag::Track> m_tracks;
    int m_currentIndex = -1;
};

