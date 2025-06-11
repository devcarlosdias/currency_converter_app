import 'package:currency_converter_app/features/home/domain/entity/supported_currency.dart';

abstract class SupportedState {}

class SupportedSuccess extends SupportedState {
  final List<SupportedCurrency> list;

  SupportedSuccess(this.list);
}

class SupportedStart extends SupportedState {}

class SupportedLoading extends SupportedState {}

class SupportedError extends SupportedState {
  /* final FailureSearch error;
  SearchError(this.error); */
}
