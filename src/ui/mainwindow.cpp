#include "mainwindow.h"
#include <QListWidget>
#include <QLineEdit>
#include <QPushButton>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFileDialog>
#include <QLabel>
#include <QFileInfo>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
{
    setupUI();
}

MainWindow::~MainWindow()
{
}

void MainWindow::setupUI()
{
    auto centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);

    auto layout = new QVBoxLayout(centralWidget);

    m_fileList = new QListWidget;
    layout->addWidget(m_fileList);

    auto tagLayout = new QHBoxLayout;
    m_artistEdit = new QLineEdit;
    m_albumEdit = new QLineEdit;
    m_titleEdit = new QLineEdit;
    tagLayout->addWidget(new QLabel("Artist:"));
    tagLayout->addWidget(m_artistEdit);
    tagLayout->addWidget(new QLabel("Album:"));
    tagLayout->addWidget(m_albumEdit);
    tagLayout->addWidget(new QLabel("Title:"));
    tagLayout->addWidget(m_titleEdit);
    layout->addLayout(tagLayout);

    auto buttonLayout = new QHBoxLayout;
    auto openButton = new QPushButton("Open Files");
    auto saveButton = new QPushButton("Save Tags");
    buttonLayout->addWidget(openButton);
    buttonLayout->addWidget(saveButton);
    layout->addLayout(buttonLayout);

    connect(openButton, &QPushButton::clicked, this, &MainWindow::openFiles);
    connect(saveButton, &QPushButton::clicked, this, &MainWindow::saveTags);
    connect(m_fileList, &QListWidget::currentRowChanged, this, &MainWindow::updateSelectedTrack);
    connect(m_artistEdit, &QLineEdit::textChanged, this, &MainWindow::artistChanged);
    connect(m_albumEdit, &QLineEdit::textChanged, this, &MainWindow::albumChanged);
    connect(m_titleEdit, &QLineEdit::textChanged, this, &MainWindow::titleChanged);
}

void MainWindow::openFiles()
{
    auto files = QFileDialog::getOpenFileNames(this, "Select audio files", QString(),
        "Audio files (*.mp3 *.flac *.wav *.aiff *.ogg *.m4a *.mp4)");
    if (files.isEmpty())
        return;

    m_tracks.clear();
    m_tracks.reserve(files.size());
    m_fileList->clear();
    for (const auto& file : files) {
        m_fileList->addItem(QFileInfo(file).fileName());
        m_tracks.append(metatag::Track(file));
    }
    statusBar()->showMessage(QString("Loaded %1 file(s)").arg(files.size()), 3000);
}

void MainWindow::saveTags()
{
    int saved = 0;
    int failed = 0;
    QStringList failedFiles;
    for (int i = 0; i < m_tracks.size(); ++i) {
        metatag::Track& track = m_tracks[i];
        if (track.isDirty()) {
            if (track.save()) {
                saved++;
            } else {
                failed++;
                failedFiles.append(QFileInfo(track.filePath()).fileName());
            }
        }
    }
    if (saved > 0 || failed > 0) {
        QString message = QString("Saved %1 track(s)").arg(saved);
        if (failed > 0) {
            message += QString(", failed to save %1 track(s): %2").arg(failed).arg(failedFiles.join(", "));
        }
        statusBar()->showMessage(message, 5000);
    }
}

void MainWindow::updateSelectedTrack()
{
    int index = m_fileList->currentRow();
    m_currentIndex = index;
    if (index >= 0 && index < m_tracks.size()) {
        loadTrack(index);
    }
}

void MainWindow::loadTrack(int index)
{
    if (index < 0 || index >= m_tracks.size())
        return;
    
    metatag::Track& track = m_tracks[index];
    if (!track.isLoaded()) {
        if (!track.load()) {
            // Failed to load metadata
            m_artistEdit->clear();
            m_albumEdit->clear();
            m_titleEdit->clear();
            return;
        }
    }
    
    m_artistEdit->setText(track.artist());
    m_albumEdit->setText(track.album());
    m_titleEdit->setText(track.title());
}

void MainWindow::artistChanged(const QString& text)
{
    if (m_currentIndex >= 0 && m_currentIndex < m_tracks.size()) {
        m_tracks[m_currentIndex].setArtist(text);
    }
}

void MainWindow::albumChanged(const QString& text)
{
    if (m_currentIndex >= 0 && m_currentIndex < m_tracks.size()) {
        m_tracks[m_currentIndex].setAlbum(text);
    }
}

void MainWindow::titleChanged(const QString& text)
{
    if (m_currentIndex >= 0 && m_currentIndex < m_tracks.size()) {
        m_tracks[m_currentIndex].setTitle(text);
    }
}

