#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmonitor.settings')
django.setup()

from books.models import Publisher
from books.tasks import update_books_for_publisher
from django.db import transaction


def add_publishers():
    publishers_data = [
        {
            'name': "O'Reilly Media",
            'description': "One of the most well-known publishers in computer literature. Popular series: Head First, Animal Guide (books with animals on covers).",
            'website': "https://www.oreilly.com/",
            'logo_url': "https://cdn.oreillystatic.com/images/sitewide-headers/oreilly_logo_mark_red.svg",
        },
        {
            'name': "Manning Publications",
            'description': "Known for its books on programming and software development. Popular series: In Action, In Depth.",
            'website': "https://www.manning.com/",
            'logo_url': "https://images.manning.com/logo-dark.svg",
        },
        {
            'name': "Packt Publishing",
            'description': "Publishes books on a wide range of technologies, including programming, DevOps, machine learning, and cloud technologies.",
            'website': "https://www.packtpub.com/",
            'logo_url': "https://static.packt-cdn.com/images/logo-big.png",
        },
        {
            'name': "Apress",
            'description': "Specializes in books for developers, IT professionals, and students. Popular series: Expert's Voice, For Professionals by Professionals.",
            'website': "https://www.apress.com/",
            'logo_url': "https://www.apress.com/covers-universal/img/apress-logo.png",
        },
        {
            'name': "No Starch Press",
            'description': "Known for its books for beginners and advanced developers, as well as for technology enthusiasts.",
            'website': "https://nostarch.com/",
            'logo_url': "https://nostarch.com/sites/default/files/styles/uc_product/public/nsp_logo_alone.png",
        },
        {
            'name': "Wiley",
            'description': "Publishes books on programming, data analysis, machine learning, and other IT areas. Popular series: For Dummies, Wrox Programmer to Programmer.",
            'website': "https://www.wiley.com/",
            'logo_url': "https://www.wiley.com/etc.clientlibs/wiley/clientlibs/clientlib-site/resources/images/wiley-logo.svg",
        },
        {
            'name': "Piter",
            'description': "One of the largest Russian publishers of books on programming, IT, and computer science. Popular series: Programmer's Library, Computer Science Classics.",
            'website': "https://www.piter.com/",
            'logo_url': "https://www.piter.com/static/img/logo.svg",
        },
        {
            'name': "DMK Press",
            'description': "Specializes in books on programming, electronics, and IT.",
            'website': "https://dmkpress.com/",
            'logo_url': "https://dmkpress.com/images/site/logo.png",
        },
    ]

    with transaction.atomic():
        for publisher_data in publishers_data:
            publisher, created = Publisher.objects.get_or_create(
                name=publisher_data['name'],
                defaults=publisher_data
            )
            if created:
                print(f"Added publisher: {publisher.name}")
            else:
                print(f"Publisher already exists: {publisher.name}")

    return Publisher.objects.all()


def update_all_books():
    publishers = Publisher.objects.all()
    for publisher in publishers:
        print(f"Starting book update for publisher: {publisher.name}")
        update_books_for_publisher(publisher.id)
    print(f"Book update started for {publishers.count()} publishers")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage_books.py [add_publishers|update_books]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "add_publishers":
        add_publishers()
    elif command == "update_books":
        update_all_books()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: add_publishers, update_books")
        sys.exit(1)