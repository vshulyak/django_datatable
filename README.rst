=======================
django_datatable
=======================

Overview
========

django-datatable is an app to make the integration of DataTables easier in CBV-fasion.

Installation
============

To install, run the following command from this directory::

	python setup.py install

Or, put `django_datatable` somewhere on your Python path.
	
Usage
=====

#. Install the module
#. Install datatables js on your page in the usual way
#. Inherit your CBV from the view ``DataTableListView`` provided by this app
#. Define so-called Presenter which lets you customize values your datatable has. Additionally, there is a possibility of filtering and ordering customization according to your needs.
#. Profit!

See tests/views.py for example usage.


